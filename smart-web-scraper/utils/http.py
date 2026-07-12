"""
Thin wrapper around requests.Session that adds retry-with-backoff behaviour
and turns the various things that can go wrong on the network (timeouts,
connection errors, bad status codes) into a single ScraperNetworkError so
callers don't need to know about requests' exception hierarchy.
"""
import time

import requests

from config.settings import (
    MAX_RETRIES,
    REQUEST_TIMEOUT_SECONDS,
    RETRY_BACKOFF_SECONDS,
    USER_AGENT,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class ScraperNetworkError(Exception):
    """Raised when a page can't be fetched after all retries are exhausted."""


def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_page(url: str, session: requests.Session = None) -> str:
    """
    Fetches a URL and returns the raw HTML, retrying on transient failures
    with exponential backoff. Raises ScraperNetworkError if every attempt
    fails.
    """
    owns_session = session is None
    session = session or build_session()

    last_error = None

    try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
                response.raise_for_status()
                return response.text

            except requests.exceptions.Timeout as error:
                last_error = error
                logger.warning(f"Timeout on attempt {attempt}/{MAX_RETRIES} for {url}")

            except requests.exceptions.ConnectionError as error:
                last_error = error
                logger.warning(f"Connection error on attempt {attempt}/{MAX_RETRIES} for {url}")

            except requests.exceptions.HTTPError as error:
                status = error.response.status_code if error.response is not None else "unknown"
                logger.warning(f"HTTP {status} on attempt {attempt}/{MAX_RETRIES} for {url}")
                last_error = error
                if error.response is not None and error.response.status_code == 404:
                    # Retrying a genuine 404 won't help, so fail fast.
                    break

            except requests.exceptions.RequestException as error:
                last_error = error
                logger.warning(f"Request failed on attempt {attempt}/{MAX_RETRIES} for {url}: {error}")

            if attempt < MAX_RETRIES:
                sleep_time = RETRY_BACKOFF_SECONDS * attempt
                time.sleep(sleep_time)

        raise ScraperNetworkError(f"Failed to fetch {url} after {MAX_RETRIES} attempts: {last_error}")

    finally:
        if owns_session:
            session.close()
