# Smart Web Scraper
A Python based web scraping tool that extracts data using keyword search and exports results into CSV, Excel & JSON format.

A keyword-driven product scraper built with Python, `requests`, and `BeautifulSoup`, with a Selenium fallback for JavaScript-rendered pages. Built as a portfolio project to demonstrate clean, modular Python architecture — not a one-off script.

The scraper targets [books.toscrape.com](https://books.toscrape.com), a sandbox site built specifically for scraping practice, so every run in this repo works against a real, live, permission-granted target rather than mocked data.

## Features

- **Keyword search** across the entire product catalogue, crawled category by category
- **Static scraping** via `requests` + `BeautifulSoup` for the (fully server-rendered) target site
- **Dynamic scraping** via Selenium for pages that require JavaScript execution, demoed against `quotes.toscrape.com/js`
- **Automatic retries with exponential backoff** on timeouts, connection errors, and transient HTTP failures
- **Three export formats**: CSV, Excel (`.xlsx`), and JSON
- **Structured logging** to both console and a timestamped log file per run
- **CLI interface** built with `argparse`
- **Offline unit tests** for the parsing logic using a saved HTML fixture, so tests don't depend on network access

Extracted fields per product: name, price, rating, product URL, image URL, availability, category.
## Tech Stack
- Python
BeautifulSoup4
Selenium
Pandas
OpenPyXl
lxml

## Project Structure

```
smart-web-scraper/
│
├── scraper/
│   ├── static_scraper.py    # requests + BeautifulSoup crawl logic
│   ├── dynamic_scraper.py   # Selenium scraper for JS-rendered pages
│   ├── parser.py            # pure HTML-parsing functions (no I/O)
│   ├── exporter.py          # CSV / Excel / JSON export
│   └── models.py            # Product dataclass
│
├── config/
│   └── settings.py          # loads .env into typed constants
│
├── utils/
│   ├── http.py               # retry-aware HTTP client
│   ├── logger.py             # console + file logging setup
│   └── helpers.py            # URL validation, text cleanup
│
├── tests/
│   ├── fixture_category_page.html
│   └── test_parser.py
│
├── logs/                     # generated at runtime, one file per run
├── output/                   # generated at runtime, exported data lands here
├── scraper.py                # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

```bash
git clone https://github.com/<your-username>/smart-web-scraper.git
cd smart-web-scraper

python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
```

Selenium needs a Chrome installation on your machine; `webdriver-manager` handles downloading the matching driver automatically the first time `--demo-dynamic` runs.

## Usage

**Search by keyword, export to CSV (default):**
```bash
python scraper.py --keyword "history"
```

**Search and export to Excel:**
```bash
python scraper.py --keyword "mystery" --output excel
```

**Search and export to JSON, capping results:**
```bash
python scraper.py --keyword "love" --output json --max-results 25
```

**Control how deep each category is crawled:**
```bash
python scraper.py --keyword "science" --max-pages-per-category 5
```

**Run the Selenium dynamic-scraping demo** (proves the JS-rendering path works, independent of the keyword search):
```bash
python scraper.py --demo-dynamic
```

All CLI options:

| Flag | Description | Default |
|---|---|---|
| `--keyword` | Search term to match against product names | required (unless `--demo-dynamic`) |
| `--output` | `csv`, `excel`, or `json` | `csv` |
| `--max-results` | Stop once this many matches are found | `100` |
| `--max-pages-per-category` | Pagination depth per category | `3` |
| `--demo-dynamic` | Run the Selenium demo instead of a keyword search | off |

## Sample Output

```
$ python scraper.py --keyword "history" --output csv

2026-07-12 09:14:02 | INFO | main | Scrape started for keyword='history', output=csv
2026-07-12 09:14:03 | INFO | scraper.static_scraper | Discovered 50 categories to search
2026-07-12 09:14:05 | INFO | scraper.static_scraper | 'History' page 1: found 20 products
2026-07-12 09:14:05 | INFO | scraper.static_scraper | 'History' contributed 20 match(es) for 'history'
2026-07-12 09:14:07 | INFO | main | Scrape finished. Total products scraped: 20. Duration: 5.41s

Found 20 product(s) matching 'history'
Results saved to: output/history_20260712_091407.csv
Time taken: 5.41s
```

Resulting CSV row:

```
name,price,rating,product_url,image_url,availability,category
The Great Railway Bazaar,£30.54,1,https://books.toscrape.com/catalogue/...,https://books.toscrape.com/media/...jpg,In stock,History
```

## Screenshots
Screenshots [Terminal Output]"C:\Users\Shilpy\Pictures\Screenshots\Screenshot (1).png"
            [CSV Output]"C:\Users\Shilpy\Pictures\Screenshots\Screenshot (2).png"
            [JSON Output]"C:\Users\Shilpy\Pictures\Screenshots\Screenshot (3).png"
Run a search locally and add your own terminal/output screenshots here — this repo intentionally doesn't ship fabricated screenshots.

## Error Handling

- `BASE_URL` is validated as a well-formed `http(s)` URL before any request is made; a malformed value in `.env` fails fast with a clear message instead of a confusing network error
- Empty or whitespace-only `--keyword` values are rejected before any crawling starts
- Network failures (timeouts, connection errors, 5xx responses) are retried up to `MAX_RETRIES` times with exponential backoff before the run gives up gracefully
- A genuine 404 fails fast instead of being retried
- A category page that returns zero products stops that category early instead of continuing to paginate through what's likely a dead end
- Missing HTML elements on a product card are logged and skipped rather than crashing the whole run
- Any unexpected exception is caught at the top level, logged in full (with stack trace) to the log file, and shown to the user as a short, readable message rather than a raw traceback
- `Ctrl+C` during a run exits cleanly instead of dumping a `KeyboardInterrupt` trace
- Every run writes a full log file to `logs/` with start time, end time, total products scraped, warnings, and errors

## Running Tests

```bash
pytest tests/ -v
```

- `test_parser.py` — HTML parsing correctness, run against a saved fixture that mirrors the real site's markup
- `test_exporter.py` — CSV/Excel/JSON output correctness, empty-list handling, filename sanitization
- `test_http.py` — retry/backoff behaviour under timeouts, connection errors, and HTTP error codes, using a fake session so no real network calls are made

All of it runs entirely offline, so tests don't depend on network access or the live site staying unchanged.

## Ethical Scraping Notes

This project only scrapes [books.toscrape.com](https://books.toscrape.com) and [quotes.toscrape.com](https://quotes.toscrape.com), both of which are built and hosted specifically for scraping practice with no `robots.txt` restrictions. The scraper:

- Sends a descriptive `User-Agent` identifying itself
- Applies a configurable delay between requests (`REQUEST_DELAY_SECONDS`)
- Does not attempt to bypass authentication, CAPTCHAs, or any access controls

To point this project at a different site, check that site's `robots.txt` and terms of service first.

## Future Improvements

- Async requests (`httpx` + `asyncio`) to speed up large multi-category crawls
- Proxy rotation support for larger-scale scraping
- A small Flask/FastAPI wrapper to expose the scraper as an API
- Persist results to SQLite/Postgres instead of flat files
- Scrapy migration for built-in throttling, caching, and pipelines
## Author 
CodesByShi