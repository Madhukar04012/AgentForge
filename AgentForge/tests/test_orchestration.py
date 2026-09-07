"""Tests for orchestration helpers."""

from __future__ import annotations

import pytest

from agentforge.orchestration.retry import RetryPolicy, retry


def test_retry_succeeds_after_failure() -> None:
    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise RuntimeError("boom")
        return "ok"

    result = retry(flaky, RetryPolicy(max_attempts=3, initial_delay=0))
    assert result == "ok"
    assert calls["n"] == 2


def test_retry_gives_up() -> None:
    def always_fail() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        retry(always_fail, RetryPolicy(max_attempts=2, initial_delay=0))


def test_retry_only_catches_configured() -> None:
    def keyerror() -> None:
        raise KeyError("k")

    with pytest.raises(KeyError):
        retry(keyerror, RetryPolicy(max_attempts=3, initial_delay=0), retry_on=(ValueError,))