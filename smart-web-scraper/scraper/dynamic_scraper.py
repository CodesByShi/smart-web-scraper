"""
Selenium-based scraper for pages that render their content with
JavaScript, where a plain requests.get() would just return an empty shell.

books.toscrape.com itself is fully server-rendered so static_scraper.py
handles it directly, but quotes.toscrape.com/js - built by the same team
specifically to demo JS-rendered scraping - is used here to show the
Selenium path actually works end to end.

This module is intentionally isolated from static_scraper.py: it's only
imported when --dynamic is passed on the CLI, so running the normal
keyword search doesn't require a Chrome installation.
"""
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config.settings import REQUEST_TIMEOUT_SECONDS, USER_AGENT
from utils.helpers import clean_text
from utils.logger import get_logger

logger = get_logger(__name__)


def _build_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(f"user-agent={USER_AGENT}")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def fetch_rendered_html(url: str, wait_for_selector: str) -> str:
    """
    Loads a page in headless Chrome, waits for a specific element to appear
    (proof that the JS has finished rendering the content), and returns the
    fully rendered page source.
    """
    driver = None
    try:
        driver = _build_driver()
        driver.get(url)

        WebDriverWait(driver, REQUEST_TIMEOUT_SECONDS).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
        )
        return driver.page_source

    except TimeoutException as error:
        logger.error(f"Timed out waiting for '{wait_for_selector}' on {url}: {error}")
        raise

    except WebDriverException as error:
        logger.error(f"Selenium failed to load {url}: {error}")
        raise

    finally:
        if driver is not None:
            driver.quit()


def scrape_js_rendered_quotes(base_url: str = "https://quotes.toscrape.com/js") -> list[dict]:
    """
    Demo entry point showing the dynamic scraper against a real
    JS-rendered page. quotes.toscrape.com/js loads its quotes via a
    script tag after the initial page load, so a plain requests.get()
    would return no quote content at all - Selenium is required here.
    """
    html = fetch_rendered_html(base_url, wait_for_selector="div.quote")

    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    quotes = []
    for quote_block in soup.select("div.quote"):
        text = clean_text(quote_block.select_one("span.text").get_text())
        author = clean_text(quote_block.select_one("small.author").get_text())
        tags = [clean_text(tag.get_text()) for tag in quote_block.select("div.tags a.tag")]
        quotes.append({"text": text, "author": author, "tags": tags})

    logger.info(f"Rendered and extracted {len(quotes)} quotes from {base_url}")
    return quotes
