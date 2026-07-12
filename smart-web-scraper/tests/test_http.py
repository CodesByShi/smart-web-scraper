"""
Tests for utils/http.py. A fake requests.Session stand-in is used so these
tests exercise the real retry/backoff logic without making actual network
calls or waiting through real sleep() delays.
"""
import requests
import pytest

import utils.http as http_module
from utils.http import ScraperNetworkError, fetch_page


class FakeResponse:
    def __init__(self, status_code=200, text="<html>ok</html>"):
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            error = requests.exceptions.HTTPError(f"{self.status_code} error")
            error.response = self
            raise error


class FakeSession:
    """Replays a scripted sequence of responses/exceptions, one per call to get()."""

    def __init__(self, script):
        self.script = list(script)
        self.call_count = 0

    def get(self, url, timeout):
        self.call_count += 1
        outcome = self.script.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def close(self):
        pass


@pytest.fixture(autouse=True)
def no_real_sleep(monkeypatch):
    # Retry backoff would otherwise slow the test suite down for no reason.
    monkeypatch.setattr(http_module.time, "sleep", lambda seconds: None)


def test_succeeds_on_first_attempt():
    session = FakeSession([FakeResponse(200, "<html>page one</html>")])
    result = fetch_page("https://example.test/page", session=session)
    assert result == "<html>page one</html>"
    assert session.call_count == 1


def test_retries_after_connection_error_then_succeeds():
    session = FakeSession(
        [
            requests.exceptions.ConnectionError("connection refused"),
            FakeResponse(200, "<html>recovered</html>"),
        ]
    )
    result = fetch_page("https://example.test/page", session=session)
    assert result == "<html>recovered</html>"
    assert session.call_count == 2


def test_retries_after_timeout_then_succeeds():
    session = FakeSession(
        [
            requests.exceptions.Timeout("timed out"),
            requests.exceptions.Timeout("timed out again"),
            FakeResponse(200, "<html>third time lucky</html>"),
        ]
    )
    result = fetch_page("https://example.test/page", session=session)
    assert result == "<html>third time lucky</html>"
    assert session.call_count == 3


def test_raises_scraper_network_error_after_exhausting_retries():
    session = FakeSession(
        [
            requests.exceptions.ConnectionError("down"),
            requests.exceptions.ConnectionError("still down"),
            requests.exceptions.ConnectionError("still down"),
        ]
    )
    with pytest.raises(ScraperNetworkError):
        fetch_page("https://example.test/page", session=session)
    assert session.call_count == 3


def test_404_fails_fast_without_exhausting_all_retries():
    session = FakeSession([FakeResponse(404, "")])
    with pytest.raises(ScraperNetworkError):
        fetch_page("https://example.test/missing", session=session)
    assert session.call_count == 1


def test_500_is_retried_unlike_404():
    session = FakeSession([FakeResponse(500, ""), FakeResponse(500, ""), FakeResponse(500, "")])
    with pytest.raises(ScraperNetworkError):
        fetch_page("https://example.test/broken", session=session)
    assert session.call_count == 3
