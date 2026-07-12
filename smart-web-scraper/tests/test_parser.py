"""
Tests for scraper/parser.py. These run entirely offline against a saved
HTML fixture that mirrors the real structure of books.toscrape.com, so the
parsing logic can be verified without depending on the live site.
"""
import os

import pytest

from scraper.parser import find_next_page_url, parse_category_links, parse_product_listing_page

FIXTURE_PATH = os.path.join(os.path.dirname(__file__), "fixture_category_page.html")
PAGE_URL = "https://books.toscrape.com/catalogue/category/books/travel_2/index.html"


@pytest.fixture
def category_page_html():
    with open(FIXTURE_PATH, encoding="utf-8") as file:
        return file.read()


def test_parses_all_products_on_page(category_page_html):
    products = parse_product_listing_page(category_page_html, PAGE_URL, category="Travel")
    assert len(products) == 2


def test_extracts_full_title_from_title_attribute(category_page_html):
    products = parse_product_listing_page(category_page_html, PAGE_URL, category="Travel")
    assert products[0].name == "A Light in the Attic"


def test_resolves_relative_urls_to_absolute(category_page_html):
    products = parse_product_listing_page(category_page_html, PAGE_URL, category="Travel")
    assert products[0].product_url.startswith("https://books.toscrape.com/")
    assert products[0].image_url.startswith("https://books.toscrape.com/")


def test_converts_star_rating_word_to_number(category_page_html):
    products = parse_product_listing_page(category_page_html, PAGE_URL, category="Travel")
    assert products[0].rating == "3"
    assert products[1].rating == "1"


def test_tags_products_with_given_category(category_page_html):
    products = parse_product_listing_page(category_page_html, PAGE_URL, category="Travel")
    assert all(p.category == "Travel" for p in products)


def test_finds_next_page_url(category_page_html):
    next_url = find_next_page_url(category_page_html, PAGE_URL)
    assert next_url == "https://books.toscrape.com/catalogue/category/books/travel_2/page-2.html"


def test_returns_none_when_no_next_page():
    html_without_pagination = "<html><body><ol class='row'></ol></body></html>"
    assert find_next_page_url(html_without_pagination, PAGE_URL) is None


def test_parses_category_sidebar_links(category_page_html):
    categories = parse_category_links(category_page_html, "https://books.toscrape.com")
    assert "Travel" in categories
    assert "Mystery" in categories
    assert categories["Travel"].startswith("https://books.toscrape.com/")
