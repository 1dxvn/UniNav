from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import time

import pytest

from scripts.codex_continuity import (
    ChildProcess, ProcessLock, Supervisor, failure_kind, quota_reset,
    read_json, read_rate_limits, validate_result, write_json,
)


THREAD = "0199a213-81c0-7800-8aa1-bbab2a035a53"


@pytest.fixture
def fake_codex(tmp_path):
    script = tmp_path / "fake_codex.py"
    script.write_text('''
import json, pathlib, subprocess, sys, time
base = pathlib.Path(__file__).parent
args = sys.argv[1:]
def emit(value):
    print(json.dumps(value), flush=True)
if "app-server" in args:
    for line in sys.stdin:
        request = json.loads(line)
        if request["method"] == "initialize":
            emit({"id": request["id"], "result": {"userAgent": "test"}})
        elif request["method"] == "account/rateLimits/read":
            emit({"id": request["id"], "result": {"rateLimits": {
                "primary": {"usedPercent": 100, "resetsAt": time.time() + 20}}}})
        elif request["method"] != "initialized":
            raise AssertionError("Unexpected account operation")
    sys.exit(0)
sys.stdin.read()
calls_path = base / "calls.json"
calls = json.loads(calls_path.read_text()) if calls_path.exists() else []
calls.append(args)
calls_path.write_text(json.dumps(calls))
emit({"type": "thread.started", "thread_id": "0199a213-81c0-7800-8aa1-bbab2a035a53"})
emit({"type": "turn.started"})
mode = (base / "mode").read_text()
if mode == "sleep":
    descendant = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    (base / "descendant.pid").write_text(str(descendant.pid))
    time.sleep(60)
if mode == "quota" and len(calls) == 1:
    emit({"type": "turn.failed", "error": {"message": "Usage limit reached", "codexErrorInfo": "usageLimitExceeded"}})
    sys.exit(1)
if mode == "auth":
    emit({"type": "turn.failed", "error": {"message": "Unauthorized: authentication failed"}})
    sys.exit(1)
status = "continue" if mode == "continue" and len(calls) == 1 else "complete"
result = {"status": status, "summary": "Checked", "next_step": "Next milestone",
          "evidence": ["test passed"], "blockers": [], "wait_seconds": 0}
pathlib.Path(args[args.index("-o") + 1]).write_text(json.dumps(result))
emit({"type": "turn.completed"})
''', encoding="utf-8")
    (tmp_path / "mode").write_text("quota")
    return [sys.executable, str(script)]


class InstantSupervisor(Supervisor):
    def __init__(self, *args):
        super().__init__(*args)
        self.waits = []

    def wait(self, until, status, reason):
        self.waits.append((until, status, reason))
        self.save(status=status, next_attempt_epoch=until)
        return self.enabled()


def supervisor(tmp_path, command):
    directory = tmp_path / "state"
    write_json(directory / "control.json", {"enabled": True})
    return InstantSupervisor(tmp_path, directory, command)


def test_quota_failure_waits_and_resumes_exact_thread(tmp_path, fake_codex):
    worker = supervisor(tmp_path, fake_codex)
    worker.run()
    calls = read_json(tmp_path / "calls.json")
    assert len(calls) == 2
    assert "resume" not in calls[0]
    assert calls[1][calls[1].index("resume") + 1] == THREAD
    assert "--last" not in calls[1]
    assert worker.waits[0][1] == "waiting_quota"
    assert 0 < worker.waits[0][0] - time.time() < 40
    assert worker.state["status"] == "complete"
    assert worker.state["thread_id"] == THREAD


def test_successful_partial_turn_continues_without_user(tmp_path, fake_codex):
    (tmp_path / "mode").write_text("continue")
    worker = supervisor(tmp_path, fake_codex)
    worker.run()
    assert len(read_json(tmp_path / "calls.json")) == 2
    assert worker.waits[0][1] == "continuing"
    assert worker.state["status"] == "complete"


def test_auth_failure_does_not_loop_or_report_completion(tmp_path, fake_codex):
    (tmp_path / "mode").write_text("auth")
    worker = supervisor(tmp_path, fake_codex)
    worker.run()
    assert worker.state["status"] == "needs_attention"
    assert len(read_json(tmp_path / "calls.json")) == 1
    assert not worker.waits


def test_restart_keeps_saved_thread_and_wait(tmp_path, fake_codex):
    directory = tmp_path / "state"
    future = time.time() + 3600
    write_json(directory / "control.json", {"enabled": True})
    write_json(directory / "state.json", {"thread_id": THREAD, "status": "waiting_quota", "next_attempt_epoch": future})
    (tmp_path / "mode").write_text("complete")
    worker = InstantSupervisor(tmp_path, directory, fake_codex)
    worker.run()
    assert worker.waits[0][0] == future
    calls = read_json(tmp_path / "calls.json")
    assert calls[0][calls[0].index("resume") + 1] == THREAD
    assert worker.state["status"] == "complete"


def test_two_exhausted_windows_wait_for_both():
    payload = {"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 200},
                              "secondary": {"usedPercent": 100, "resetsAt": 500}}}
    assert quota_reset(payload, 100) == 510


def test_other_model_bucket_does_not_delay_this_worker():
    payload = {"rateLimits": {"primary": {"usedPercent": 50, "resetsAt": 200}},
               "rateLimitsByLimitId": {"other": {"primary": {"usedPercent": 100, "resetsAt": 9999}}}}
    assert quota_reset(payload, 100) is None


def test_expired_and_malformed_windows_are_ignored():
    assert quota_reset({"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 99}}}, 100) is None
    assert quota_reset({"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": "soon"}}}, 100) is None


@pytest.mark.parametrize(("message", "kind"), [
    ("usageLimitExceeded", "quota"), ("HTTP 429 rate limit", "quota"),
    ("insufficient_quota", "attention"), ("credit balance exhausted", "attention"),
    ("Unauthorized 401", "attention"),
    ("contextWindowExceeded", "context"), ("server overloaded 503", "retry"),
])
def test_failure_types(message, kind):
    assert failure_kind([message]) == kind


def test_missing_or_false_completion_is_rejected():
    result = {"status": "complete", "summary": "done", "next_step": "", "evidence": [], "blockers": [], "wait_seconds": 0}
    with pytest.raises(ValueError):
        validate_result(result)
    result.update(evidence=["build passed"], blockers=["A still missing"])
    with pytest.raises(ValueError):
        validate_result(result)
    with pytest.raises(ValueError):
        validate_result(None)


def test_account_probe_uses_public_read_endpoint(tmp_path, fake_codex):
    payload = read_rate_limits(fake_codex, tmp_path)
    assert payload["rateLimits"]["primary"]["usedPercent"] == 100


def test_lock_prevents_duplicate_supervisors_and_is_released(tmp_path):
    path = tmp_path / "worker.lock"
    with ProcessLock(path):
        with pytest.raises(RuntimeError, match="already running"):
            with ProcessLock(path):
                pass
    with ProcessLock(path):
        pass


def test_disabled_supervisor_does_not_start_a_worker(tmp_path, fake_codex):
    worker = supervisor(tmp_path, fake_codex)
    write_json(worker.directory / "control.json", {"enabled": False})
    worker.run()
    assert worker.state["status"] == "stopped"
    assert not (tmp_path / "calls.json").exists()


def test_stop_interrupts_long_wait(tmp_path, fake_codex):
    worker = supervisor(tmp_path, fake_codex)
    write_json(worker.directory / "control.json", {"enabled": False})
    assert Supervisor.wait(worker, time.time() + 3600, "waiting_quota", "test") is False


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process tree lifecycle")
def test_windows_job_terminates_descendants(tmp_path):
    import ctypes
    from ctypes import wintypes
    pid_file = tmp_path / "child.pid"
    code = "import pathlib,subprocess,sys,time; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); pathlib.Path(sys.argv[1]).write_text(str(p.pid)); time.sleep(60)"
    child = ChildProcess([sys.executable, "-c", code, str(pid_file)], tmp_path)
    deadline = time.monotonic() + 10
    while not pid_file.exists() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert pid_file.exists()
    pid = int(pid_file.read_text())
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenProcess(0x100000, False, pid)
    assert handle
    try:
        child.close()
        assert kernel.WaitForSingleObject(handle, 5000) == 0
    finally:
        kernel.CloseHandle(handle)
