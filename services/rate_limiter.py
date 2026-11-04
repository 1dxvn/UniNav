from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, status

from config import LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS


class FailureRateLimiter:
    def __init__(self, max_failures: int, window_seconds: int) -> None:
        self._max_failures: int = max_failures
        self._window_seconds: int = window_seconds
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock: threading.Lock = threading.Lock()

    def ensure_allowed(self, key: str) -> None:
        with self._lock:
            recent = self._recent_failures(key)
            if len(recent) >= self._max_failures:
                retry_after = int(recent[0] + self._window_seconds - time.monotonic()) + 1
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Try again later.",
                    headers={"Retry-After": str(max(retry_after, 1))},
                )

    def register_failure(self, key: str) -> None:
        with self._lock:
            self._recent_failures(key).append(time.monotonic())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def _recent_failures(self, key: str) -> deque[float]:
        failures = self._failures[key]
        cutoff = time.monotonic() - self._window_seconds
        while failures and failures[0] < cutoff:
            failures.popleft()
        return failures


login_rate_limiter: FailureRateLimiter = FailureRateLimiter(
    LOGIN_MAX_FAILURES, LOGIN_WINDOW_SECONDS
)
