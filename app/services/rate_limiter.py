"""Caps how many replies the server generates in an hour."""

import threading
import time
from collections import deque
from collections.abc import Callable

from app.exceptions import RateLimitExceededError

SECONDS_PER_HOUR = 3600
NO_LIMIT = 0


class RequestRateLimiter:
    """Counts the requests of the last hour and refuses the ones beyond the limit.

    The count is for the whole server rather than for each visitor: what it protects is the
    credit of the account behind the API, and a count per visitor would have to read the address
    from a header that only the proxy in front of the server is trusted to write. The timestamps
    are kept in memory, so restarting the server starts the count again.

    A limit of zero or less turns the cap off, which is what a run on a local model wants.
    """

    def __init__(
        self,
        max_requests: int,
        window_s: float = SECONDS_PER_HOUR,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._max_requests = max_requests
        self._window_s = window_s
        self._clock = clock
        # Routes run in a thread pool, so two requests can reach the limiter at the same moment.
        self._lock = threading.Lock()
        self._accepted_at: deque[float] = deque()

    def record_request(self) -> None:
        """Count one request, or raise RateLimitExceededError when the limit is already reached."""
        if self._max_requests <= NO_LIMIT:
            return

        now = self._clock()
        with self._lock:
            self._forget_before(now - self._window_s)
            if len(self._accepted_at) >= self._max_requests:
                raise RateLimitExceededError(self._seconds_until_free(now))
            self._accepted_at.append(now)

    def _forget_before(self, limit: float) -> None:
        """Drop the requests that left the window, so only the recent ones are counted."""
        while self._accepted_at and self._accepted_at[0] <= limit:
            self._accepted_at.popleft()

    def _seconds_until_free(self, now: float) -> int:
        """Return how long until the oldest counted request leaves the window."""
        return max(1, round(self._accepted_at[0] + self._window_s - now))
