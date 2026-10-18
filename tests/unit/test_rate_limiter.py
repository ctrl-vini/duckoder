"""Tests for the cap on how many replies the server generates in an hour."""

from collections.abc import Callable

import pytest

from app.exceptions import RateLimitExceededError
from app.services.rate_limiter import RequestRateLimiter

WINDOW_S = 60.0


def clock_at(readings: list[float]) -> Callable[[], float]:
    """Clock that returns each reading in turn, so a test can move time forward."""
    return iter(readings).__next__


def test_requests_within_the_limit_are_counted() -> None:
    limiter = RequestRateLimiter(max_requests=2, window_s=WINDOW_S, clock=clock_at([0.0, 1.0]))

    limiter.record_request()
    limiter.record_request()


def test_the_request_past_the_limit_is_refused() -> None:
    limiter = RequestRateLimiter(max_requests=2, window_s=WINDOW_S, clock=clock_at([0.0, 1.0, 2.0]))
    limiter.record_request()
    limiter.record_request()

    with pytest.raises(RateLimitExceededError) as raised:
        limiter.record_request()

    # The oldest counted request was made at 0.0, so the window frees up 58 s after 2.0.
    assert raised.value.retry_after_s == 58


def test_requests_that_left_the_window_are_forgotten() -> None:
    limiter = RequestRateLimiter(max_requests=1, window_s=WINDOW_S, clock=clock_at([0.0, 61.0]))
    limiter.record_request()

    limiter.record_request()


def test_a_limit_of_zero_turns_the_cap_off() -> None:
    limiter = RequestRateLimiter(max_requests=0, window_s=WINDOW_S, clock=clock_at([0.0]))

    for _ in range(5):
        limiter.record_request()
