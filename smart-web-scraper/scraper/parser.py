"""
Turns raw HTML from books.toscrape.com into Product objects. Kept separate
from static_scraper.py so the parsing logic can be unit tested without
making any real HTTP requests.
"""
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from scraper.models import Product
from utils.helpers import clean_text
from utils.logger import get_logger

logger = get_logger(__name__)

RATING_WORD_TO_NUMBER = {
    "One": "1",
    "Two": "2",
    "Three": "3",
    "Four": "4",
    "Five": "5",
}


def extract_rating(product_pod) -> str:
    rating_tag = product_pod.select_one("p.star-rating")
    if not rating_tag:
        return "Not rated"

    rating_classes = rating_tag.get("class", [])
    rating_word = next((cls for cls in rating_classes if cls != "star-rating"), None)
    return RATING_WORD_TO_NUMBER.get(rating_word, "Not rated")


def extract_availability(product_pod) -> str:
    availability_tag = product_pod.select_one("p.instock.availability")
    if not availability_tag:
        return "Unknown"
    text = clean_text(availability_tag.get_text())
    return text if text else "Unknown"


def parse_product_listing_page(html: str, page_url: str, category: str) -> list[Product]:
    """
    Parses a single catalogue listing page (either the homepage or a
    category page) and returns every product found on it, tagged with the
    category that was being crawled when the page was fetched.
    """
    soup = BeautifulSoup(html, "lxml")
    product_pods = soup.select("article.product_pod")

    products = []
    for pod in product_pods:
        try:
            title_tag = pod.select_one("h3 a")
            image_tag = pod.select_one("div.image_container img")
            price_tag = pod.select_one("p.price_color")

            if not title_tag or not price_tag:
                logger.warning(f"Skipping a product pod missing required fields on {page_url}")
                continue

            name = title_tag.get("title") or clean_text(title_tag.get_text())
            product_url = urljoin(page_url, title_tag.get("href", ""))
            image_url = urljoin(page_url, image_tag.get("src")) if image_tag else ""
            price = clean_text(price_tag.get_text())

            products.append(
                Product(
                    name=name,
                    price=price,
                    rating=extract_rating(pod),
                    product_url=product_url,
                    image_url=image_url,
                    availability=extract_availability(pod),
                    category=category,
                )
            )
        except Exception as error:
            logger.error(f"Failed to parse a product pod on {page_url}: {error}")
            continue

    return products


def find_next_page_url(html: str, current_page_url: str) -> str | None:
    soup = BeautifulSoup(html, "lxml")
    next_link = soup.select_one("li.next a")
    if not next_link or not next_link.get("href"):
        return None
    return urljoin(current_page_url, next_link["href"])


def parse_category_links(homepage_html: str, base_url: str) -> dict[str, str]:
    """Returns {category_name: category_url} pulled from the homepage sidebar."""
    soup = BeautifulSoup(homepage_html, "lxml")
    category_links = soup.select("div.side_categories ul li ul li a")

    categories = {}
    for link in category_links:
        name = clean_text(link.get_text())
        url = urljoin(base_url, link.get("href", ""))
        if name:
            categories[name] = url

    return categories
