"""Local, resumable Codex worker. No API keys or extra dependencies required."""
from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
from pathlib import Path
import queue
import shutil
import subprocess
import threading
import time
import uuid
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "scripts" / "continuity-result.schema.json"
PROMPT = ROOT / "EJECUCION_AUTONOMA.md"
STATUSES = {"continue", "waiting", "complete", "blocked"}
IDLE_TIMEOUT_SECONDS = 30 * 60


def utc(timestamp: float | None = None) -> str:
    return datetime.fromtimestamp(timestamp or time.time(), timezone.utc).isoformat()


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return default


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def codex_command() -> list[str]:
    """Avoid cmd.exe and shell interpolation, including with npm on Windows."""
    executable = shutil.which("codex.exe") or shutil.which("codex")
    if not executable:
        raise RuntimeError("Codex CLI is not installed or is missing from PATH.")
    if Path(executable).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        package = Path(executable).parent / "node_modules" / "@openai" / "codex"
        # Prefer the native binary so the process belongs directly to our job.
        import platform
        architecture = "arm64" if platform.machine().lower() in {"arm64", "aarch64"} else "x64"
        triple = f"{'aarch64' if architecture == 'arm64' else 'x86_64'}-pc-windows-msvc"
        vendor_paths = [package / "node_modules" / "@openai" / f"codex-win32-{architecture}",
                        package.parent / f"codex-win32-{architecture}", package]
        for vendor in vendor_paths:
            native = vendor / "vendor" / triple / "bin" / "codex.exe"
            if native.is_file():
                return [str(native)]
        entrypoint = package / "bin" / "codex.js"
        node = shutil.which("node.exe") or shutil.which("node")
        if node and entrypoint.is_file():
            return [node, str(entrypoint)]
        raise RuntimeError("Cannot resolve the native Codex binary or npm entrypoint.")
    return [executable]


class ProcessLock:
    """An OS lock, released after a crash; stale PID files cannot block restart."""
    def __init__(self, path: Path):
        self.path = path
        self.file = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.file = self.path.open("a+b")
        self.file.seek(0, os.SEEK_END)
        if not self.file.tell():
            self.file.write(b"0")
            self.file.flush()
        self.file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(self.file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.file.close()
            raise RuntimeError("Another continuity supervisor is already running.") from None
        return self

    def __exit__(self, *_):
        self.file.close()


class ChildProcess:
    """Kill the entire Windows child tree if its supervisor exits or crashes."""
    def __init__(self, command, cwd, **kwargs):
        self.job = None
        options = {"encoding": "utf-8", "errors": "replace", "text": True, **kwargs}
        if os.name == "nt":
            options["creationflags"] = subprocess.CREATE_NO_WINDOW
        self.process = subprocess.Popen(command, cwd=cwd, **options)
        if os.name == "nt":
            from ctypes import wintypes

            class BasicLimits(ctypes.Structure):
                _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                            ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                            ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                            ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                            ("scheduling", wintypes.DWORD)]

            class ExtendedLimits(ctypes.Structure):
                _fields_ = [("basic", BasicLimits), ("io", ctypes.c_uint64 * 6),
                            ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                            ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CreateJobObjectW.restype = wintypes.HANDLE
            kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
            kernel.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
            kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
            kernel.CloseHandle.argtypes = [wintypes.HANDLE]
            handle = kernel.CreateJobObjectW(None, None)
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if not handle or not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)) or not kernel.AssignProcessToJobObject(handle, int(self.process._handle)):
                error = ctypes.get_last_error()
                self.process.kill()
                self.process.wait()
                if handle:
                    kernel.CloseHandle(handle)
                raise OSError(error, "Cannot isolate the Codex process tree in a Windows job.")
            self.job = (kernel, handle)

    def close(self):
        if self.job:
            self.job[0].CloseHandle(self.job[1])
            self.job = None
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=10)
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            if stream:
                stream.close()


def collect_lines(stream, messages: queue.Queue) -> None:
    try:
        for line in stream:
            messages.put(line)
    finally:
        messages.put(None)


def read_rate_limits(command: list[str], cwd: Path, timeout: float = 30) -> dict:
    """Only call the public account endpoint. Never read or return auth tokens."""
    child = ChildProcess(command + ["app-server", "--listen", "stdio://"], cwd,
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    messages: queue.Queue = queue.Queue()
    threading.Thread(target=collect_lines, args=(child.process.stdout, messages), daemon=True).start()

    def send(value):
        child.process.stdin.write(json.dumps(value) + "\n")
        child.process.stdin.flush()

    def response(identifier):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            line = messages.get(timeout=max(0.01, deadline - time.monotonic()))
            if line is None:
                raise RuntimeError("Codex account endpoint closed unexpectedly.")
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if value.get("id") == identifier:
                if "error" in value:
                    raise RuntimeError(value["error"].get("message", "Account endpoint failed."))
                return value["result"]
        raise TimeoutError("Codex account endpoint timed out.")

    try:
        send({"id": 1, "method": "initialize", "params": {
            "clientInfo": {"name": "uninav_continuity", "version": "1.0.0"}}})
        response(1)
        send({"method": "initialized", "params": {}})
        send({"id": 2, "method": "account/rateLimits/read", "params": {}})
        return response(2)
    finally:
        child.close()


def quota_reset(payload: dict, now: float) -> float | None:
    bucket = payload.get("rateLimits")
    if not isinstance(bucket, dict):
        bucket = (payload.get("rateLimitsByLimitId") or {}).get("codex", {})
    resets = []
    for name in ("primary", "secondary"):
        window = bucket.get(name) or {}
        if not isinstance(window, dict):
            continue
        used, reset = window.get("usedPercent"), window.get("resetsAt")
        if isinstance(used, (int, float)) and isinstance(reset, (int, float)):
            if math.isfinite(reset) and used >= 100 and reset > now:
                resets.append(reset)
    return max(resets) + 10 if resets else None


def failure_kind(messages: list[str]) -> str:
    text = " ".join(messages).lower()
    if any(term in text for term in ("insufficient_quota", "credit balance", "insufficient credits", "billing hard limit")):
        return "attention"
    if any(term in text for term in ("usagelimitexceeded", "usage limit", "usage_limit", "rate limit", "rate_limit", "429", "quota")):
        return "quota"
    if any(term in text for term in ("unauthorized", "authentication", "not logged in", "401")):
        return "attention"
    if any(term in text for term in ("contextwindowexceeded", "context window", "context length", "context overflow")):
        return "context"
    if any(term in text for term in ("invalid configuration", "error loading config", "unexpected argument", "model is not available")):
        return "attention"
    return "retry"


def validate_result(value: dict) -> dict:
    if not isinstance(value, dict) or value.get("status") not in STATUSES:
        raise ValueError("Worker did not return a valid status.")
    for key in ("summary", "next_step"):
        if not isinstance(value.get(key), str):
            raise ValueError(f"Worker omitted {key}.")
    for key in ("evidence", "blockers"):
        if not isinstance(value.get(key), list) or not all(isinstance(item, str) for item in value[key]):
            raise ValueError(f"Worker omitted {key}.")
    if type(value.get("wait_seconds")) is not int or not 0 <= value["wait_seconds"] <= 86400:
        raise ValueError("Worker returned an invalid wait interval.")
    if value["status"] == "complete" and (not value["evidence"] or value["blockers"]):
        raise ValueError("Completion requires evidence and no remaining blockers.")
    return value


class Supervisor:
    def __init__(self, root: Path, directory: Path, command: list[str] | None = None):
        self.root = root
        self.directory = directory
        directory.mkdir(parents=True, exist_ok=True)
        self.command = command or codex_command()
        self.state_path = directory / "state.json"
        self.state = read_json(self.state_path, {})
        self.state.update({"pid": os.getpid(), "workspace": str(root)})

    def save(self, **changes):
        self.state.update(changes, updated_at=utc())
        write_json(self.state_path, self.state)

    def enabled(self) -> bool:
        return read_json(self.directory / "control.json", {}).get("enabled") is True

    def log(self, message: str):
        line = f"{utc()} {message}"
        with (self.directory / "supervisor.log").open("a", encoding="utf-8") as stream:
            stream.write(line + "\n")
        print(line, flush=True)

    def wait(self, until: float, status: str, reason: str) -> bool:
        self.save(status=status, reason=reason, next_attempt_at=utc(until), next_attempt_epoch=until)
        self.log(f"{status}: {reason}; next attempt {utc(until)}")
        while time.time() < until:
            if not self.enabled():
                return False
            time.sleep(min(1, max(0, until - time.time())))
        return self.enabled()

    def run_turn(self) -> tuple[int, list[str], dict | None]:
        attempt = self.state.get("attempts", 0) + 1
        prefix = self.directory / f"turn-{attempt:05d}-{uuid.uuid4().hex[:8]}"
        output = prefix.with_suffix(".result.json")
        errors = []
        args = self.command + ["--ask-for-approval", "never", "--sandbox", "danger-full-access",
                               "-C", str(self.root), "exec", "--json", "--output-schema", str(SCHEMA), "-o", str(output)]
        if self.state.get("thread_id"):
            args.extend(["resume", self.state["thread_id"]])
        args.append("-")
        prompt = PROMPT.read_text(encoding="utf-8")
        if self.state.get("last_result"):
            prompt += "\n\nLast supervisor checkpoint:\n" + json.dumps(self.state["last_result"], ensure_ascii=False)
        self.save(status="working", attempts=attempt, next_attempt_at=None, next_attempt_epoch=None,
                  reason="Running the next verified project milestone.", output_file=str(output))
        self.log(f"Starting turn {attempt}; thread {self.state.get('thread_id', 'new')}")
        with prefix.with_suffix(".stderr.log").open("w", encoding="utf-8") as stderr, \
                prefix.with_suffix(".events.jsonl").open("w", encoding="utf-8") as events:
            child = ChildProcess(args, self.root, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
            self.save(child_pid=child.process.pid)
            messages: queue.Queue = queue.Queue()
            threading.Thread(target=collect_lines, args=(child.process.stdout, messages), daemon=True).start()
            try:
                child.process.stdin.write(prompt)
                child.process.stdin.close()
                child.process.stdin = None
                ended = False
                last_output = time.monotonic()
                while not ended:
                    if not self.enabled():
                        return -1, ["Stopped by user."], None
                    try:
                        line = messages.get(timeout=1)
                    except queue.Empty:
                        if time.monotonic() - last_output >= IDLE_TIMEOUT_SECONDS:
                            return 124, ["Codex produced no events for 30 minutes; resuming its saved conversation."], None
                        continue
                    if line is None:
                        ended = True
                        continue
                    last_output = time.monotonic()
                    events.write(line)
                    events.flush()
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "thread.started":
                        identifier = str(uuid.UUID(event["thread_id"]))
                        if self.state.get("thread_id") and self.state["thread_id"] != identifier:
                            raise RuntimeError("Codex resumed a different thread; stopping to avoid duplicate work.")
                        self.save(thread_id=identifier)
                    if event.get("type") in {"error", "turn.failed"}:
                        errors.append(json.dumps(event, ensure_ascii=False))
                        errors = errors[-20:]
                    if time.monotonic() - getattr(self, "last_heartbeat", 0) >= 15:
                        self.save(last_event=event.get("type"), heartbeat_at=utc())
                        self.last_heartbeat = time.monotonic()
                code = child.process.wait()
            finally:
                child.close()
                self.save(child_pid=None)
        errors.append(prefix.with_suffix(".stderr.log").read_text(encoding="utf-8")[-12000:])
        result = None
        if code == 0:
            try:
                result = validate_result(read_json(output))
            except (ValueError, TypeError, json.JSONDecodeError) as error:
                errors.append(str(error))
                code = 1
        return code, errors, result

    def run(self):
        if self.state.get("status") in {"complete", "needs_attention"}:
            return
        self.log("Supervisor running. Command approvals: never; sandbox: danger-full-access.")
        # A scheduled restart must preserve an existing quota/backoff deadline.
        deadline = self.state.get("next_attempt_epoch", 0) or 0
        if deadline > time.time() and not self.wait(deadline, self.state.get("status", "waiting"), self.state.get("reason", "Restoring saved wait.")):
            self.save(status="stopped")
            return
        failures = 0
        while self.enabled():
            try:
                code, errors, result = self.run_turn()
                if not self.enabled():
                    break
                if code == 0 and result:
                    failures = 0
                    self.save(last_result=result, reason=result["summary"])
                    self.log(f"Worker: {result['status']}: {result['summary']}")
                    if result["status"] == "complete":
                        self.save(status="complete")
                        return
                    if result["status"] == "blocked":
                        self.save(status="needs_attention")
                        return
                    delay = max(300, result["wait_seconds"]) if result["status"] == "waiting" else 5
                    if not self.wait(time.time() + delay, "waiting" if result["status"] == "waiting" else "continuing", result["next_step"]):
                        break
                    continue
                kind = failure_kind(errors)
                failures += 1
                self.save(last_error="\n".join(errors)[-16000:])
                if kind == "attention":
                    self.save(status="needs_attention", reason="Login, credit balance or configuration requires attention. See last_error.")
                    self.log(self.state["reason"])
                    return
                if kind == "context":
                    self.save(previous_thread_id=self.state.get("thread_id"), thread_id=None)
                    self.log("Context exhausted: starting a fresh thread from project files and saved checkpoints.")
                delay = min(900, 30 * 2 ** min(failures, 5))
                until = time.time() + delay
                if kind == "quota":
                    until = time.time() + 900
                    try:
                        until = quota_reset(read_rate_limits(self.command, self.root), time.time()) or until
                    except (OSError, RuntimeError, TimeoutError, queue.Empty) as error:
                        self.log(f"Quota endpoint unavailable ({type(error).__name__}); retrying in 15 minutes.")
                if not self.wait(until, "waiting_quota" if kind == "quota" else "retrying", f"Worker failed ({kind}); conversation and files preserved."):
                    break
            except (OSError, RuntimeError, ValueError) as error:
                self.log(f"Supervisor recovery: {error}")
                if not self.wait(time.time() + 120, "retrying", str(error)):
                    break
        self.save(status="stopped", reason="Stopped by user control.", next_attempt_at=None, next_attempt_epoch=None)
        self.log("Supervisor stopped.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["run", "status", "stop", "enable", "probe"])
    parser.add_argument("--state-dir", type=Path, default=ROOT / ".uninav-continuity")
    args = parser.parse_args()
    directory = args.state_dir.resolve()
    if args.action == "status":
        print(json.dumps(read_json(directory / "state.json", {"status": "not_started"}), ensure_ascii=False, indent=2))
    elif args.action in {"stop", "enable"}:
        write_json(directory / "control.json", {"enabled": args.action == "enable", "updated_at": utc()})
        if args.action == "enable":
            state = read_json(directory / "state.json", {})
            if state.get("status") == "needs_attention":
                state.update(status="ready", reason="Explicitly restarted after attention was requested.")
                write_json(directory / "state.json", state)
        print("Continuity enabled." if args.action == "enable" else "Stop requested. The worker will terminate within a few seconds.")
    elif args.action == "probe":
        # Deliberately return only limits, never the login response or credentials.
        limits = read_rate_limits(codex_command(), ROOT)
        print(json.dumps({"rateLimits": limits.get("rateLimits"),
                          "ordinaryUsageAllowed": limits.get("ordinaryUsageAllowed")}, indent=2))
    else:
        try:
            with ProcessLock(directory / "supervisor.lock"):
                Supervisor(ROOT, directory).run()
        except RuntimeError as error:
            print(str(error), flush=True)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
