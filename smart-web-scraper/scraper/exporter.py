"""
Handles turning a list of Product objects into a file on disk. Kept as
its own module because export format is just a presentation concern -
it shouldn't know anything about how the data was scraped.
"""
import json
from datetime import datetime

import pandas as pd

from config.settings import OUTPUT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)

SUPPORTED_FORMATS = ("csv", "excel", "json")


def _build_output_path(keyword: str, extension: str) -> str:
    normalized = "_".join(keyword.strip().lower().split())
    safe_keyword = "".join(c for c in normalized if c.isalnum() or c in ("_", "-"))
    safe_keyword = safe_keyword.strip("_") or "results"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{OUTPUT_DIR}/{safe_keyword}_{timestamp}.{extension}"


def export_products(products: list, keyword: str, output_format: str) -> str:
    if output_format not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported export format '{output_format}'. Choose from {SUPPORTED_FORMATS}")

    if not products:
        logger.warning("No products to export - skipping file creation")
        return ""

    records = [product.to_dict() for product in products]

    if output_format == "csv":
        path = _build_output_path(keyword, "csv")
        pd.DataFrame(records).to_csv(path, index=False, encoding="utf-8-sig")

    elif output_format == "excel":
        path = _build_output_path(keyword, "xlsx")
        pd.DataFrame(records).to_excel(path, index=False, engine="openpyxl")

    else:  # json
        path = _build_output_path(keyword, "json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(records, file, indent=2, ensure_ascii=False)

    logger.info(f"Exported {len(records)} products to {path}")
    return path
