"""
Crawls books.toscrape.com using plain HTTP requests (no JavaScript
rendering needed - the site is fully server-rendered). This is the scraper
used for the vast majority of runs; dynamic_scraper.py only kicks in for
pages that require JS execution.
"""
import time

from config.settings import BASE_URL, REQUEST_DELAY_SECONDS
from scraper.models import Product
from scraper.parser import find_next_page_url, parse_category_links, parse_product_listing_page
from utils.helpers import is_valid_url
from utils.http import ScraperNetworkError, build_session, fetch_page
from utils.logger import get_logger

logger = get_logger(__name__)


class InvalidKeywordError(Exception):
    """Raised when the search keyword is empty or whitespace-only."""


class InvalidTargetUrlError(Exception):
    """Raised when BASE_URL in the environment isn't a well-formed http(s) URL."""


def scrape_category(category_name: str, category_url: str, session, max_pages: int) -> list[Product]:
    products = []
    current_url = category_url
    page_number = 1

    while current_url and page_number <= max_pages:
        try:
            html = fetch_page(current_url, session=session)
        except ScraperNetworkError as error:
            logger.error(f"Skipping page {page_number} of '{category_name}': {error}")
            break

        page_products = parse_product_listing_page(html, current_url, category_name)
        products.extend(page_products)
        logger.info(f"'{category_name}' page {page_number}: found {len(page_products)} products")

        if not page_products:
            logger.warning(f"'{category_name}' page {page_number} had no products - stopping this category early")
            break

        current_url = find_next_page_url(html, current_url)
        page_number += 1
        time.sleep(REQUEST_DELAY_SECONDS)

    return products


def search_products(keyword: str, max_pages_per_category: int = 3, max_results: int = 100) -> list[Product]:
    """
    Crawls the site category by category, filtering products whose name
    contains the given keyword (case-insensitive). Stops early once
    max_results matches have been collected so a search doesn't have to
    walk the entire ~1000-product catalogue every time.
    """
    if not keyword or not keyword.strip():
        raise InvalidKeywordError("Search keyword cannot be empty or whitespace-only")

    if not is_valid_url(BASE_URL):
        raise InvalidTargetUrlError(f"BASE_URL '{BASE_URL}' is not a valid http(s) URL - check your .env file")

    session = build_session()
    keyword_lower = keyword.strip().lower()
    matched_products = []

    try:
        homepage_html = fetch_page(BASE_URL, session=session)
    except ScraperNetworkError as error:
        logger.error(f"Could not reach {BASE_URL}: {error}")
        return []

    categories = parse_category_links(homepage_html, BASE_URL)
    logger.info(f"Discovered {len(categories)} categories to search")

    for category_name, category_url in categories.items():
        if len(matched_products) >= max_results:
            break

        category_products = scrape_category(category_name, category_url, session, max_pages_per_category)
        matches = [p for p in category_products if keyword_lower in p.name.lower()]

        if matches:
            logger.info(f"'{category_name}' contributed {len(matches)} match(es) for '{keyword}'")
        matched_products.extend(matches)

    session.close()
    return matched_products[:max_results]
