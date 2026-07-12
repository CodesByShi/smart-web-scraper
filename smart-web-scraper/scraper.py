"""
Command-line entry point for the smart web scraper.

Examples:
    python scraper.py --keyword "laptop" --output csv
    python scraper.py --keyword "history" --output excel --max-results 50
    python scraper.py --demo-dynamic
"""
import argparse
import sys
import time

from scraper.exporter import export_products
from scraper.static_scraper import InvalidKeywordError, InvalidTargetUrlError, search_products
from utils.logger import get_logger

logger = get_logger("main")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smart Web Scraper - keyword-based product search over books.toscrape.com",
    )
    parser.add_argument("--keyword", type=str, help="Keyword to search for, e.g. 'history' or 'love'")
    parser.add_argument(
        "--output",
        type=str,
        choices=["csv", "excel", "json"],
        default="csv",
        help="Export format for the results (default: csv)",
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of matching products to collect (default: 100)",
    )
    parser.add_argument(
        "--max-pages-per-category",
        type=int,
        default=3,
        help="Pagination depth per category while searching (default: 3)",
    )
    parser.add_argument(
        "--demo-dynamic",
        action="store_true",
        help="Run the Selenium dynamic scraper demo against a JS-rendered page instead of a keyword search",
    )
    return parser.parse_args()


def run_keyword_search(args: argparse.Namespace) -> None:
    start_time = time.time()
    logger.info(f"Scrape started for keyword='{args.keyword}', output={args.output}")

    try:
        products = search_products(
            keyword=args.keyword,
            max_pages_per_category=args.max_pages_per_category,
            max_results=args.max_results,
        )
    except (InvalidKeywordError, InvalidTargetUrlError) as error:
        logger.error(str(error))
        print(f"\nError: {error}")
        sys.exit(1)

    elapsed_seconds = round(time.time() - start_time, 2)

    if not products:
        logger.warning(f"No products matched keyword '{args.keyword}'. Nothing was exported.")
        print(f"\nNo results found for '{args.keyword}'.")
        return

    output_path = export_products(products, args.keyword, args.output)

    logger.info(f"Scrape finished. Total products scraped: {len(products)}. Duration: {elapsed_seconds}s")

    print(f"\nFound {len(products)} product(s) matching '{args.keyword}'")
    print(f"Results saved to: {output_path}")
    print(f"Time taken: {elapsed_seconds}s")


def run_dynamic_demo() -> None:
    from scraper.dynamic_scraper import scrape_js_rendered_quotes

    logger.info("Running dynamic (Selenium) scraper demo")
    quotes = scrape_js_rendered_quotes()

    print(f"\nRendered and extracted {len(quotes)} quotes from a JavaScript-rendered page:\n")
    for quote in quotes[:5]:
        print(f"  \"{quote['text']}\" — {quote['author']}")


def main() -> None:
    args = parse_arguments()

    try:
        if args.demo_dynamic:
            run_dynamic_demo()
            return

        if not args.keyword or not args.keyword.strip():
            print("Error: --keyword is required unless --demo-dynamic is used.")
            print("Example: python scraper.py --keyword \"laptop\" --output csv")
            sys.exit(1)

        run_keyword_search(args)

    except KeyboardInterrupt:
        print("\nScrape cancelled by user.")
        sys.exit(130)

    except Exception as error:
        # Anything unexpected still gets logged in full (with stack trace,
        # via logger.exception) so it's debuggable from the log file, but
        # the user sees a short, clean message instead of a raw traceback.
        logger.exception(f"Unexpected error: {error}")
        print(f"\nSomething went wrong: {error}")
        print("Check the latest log file in logs/ for full details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
