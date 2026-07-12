"""
Tests for scraper/exporter.py. Uses pytest's tmp_path fixture and monkeypatches
OUTPUT_DIR so files land in a throwaway directory instead of the real output/
folder.
"""
import csv
import json

import pandas as pd
import pytest

import scraper.exporter as exporter
from scraper.models import Product

SAMPLE_PRODUCTS = [
    Product(
        name="A Light in the Attic",
        price="£51.77",
        rating="3",
        product_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        image_url="https://books.toscrape.com/media/cache/attic.jpg",
        availability="In stock",
        category="Poetry",
    ),
    Product(
        name="Soumission",
        price="£50.10",
        rating="1",
        product_url="https://books.toscrape.com/catalogue/soumission_998/index.html",
        image_url="https://books.toscrape.com/media/cache/soumission.jpg",
        availability="In stock",
        category="Fiction",
    ),
]


@pytest.fixture(autouse=True)
def use_tmp_output_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter, "OUTPUT_DIR", str(tmp_path))


def test_export_csv_writes_correct_rows():
    path = exporter.export_products(SAMPLE_PRODUCTS, "attic", "csv")
    assert path.endswith(".csv")

    with open(path, encoding="utf-8-sig") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 2
    assert rows[0]["name"] == "A Light in the Attic"
    assert rows[0]["category"] == "Poetry"


def test_export_json_writes_correct_records():
    path = exporter.export_products(SAMPLE_PRODUCTS, "attic", "json")
    assert path.endswith(".json")

    with open(path, encoding="utf-8") as file:
        records = json.load(file)

    assert len(records) == 2
    assert records[1]["name"] == "Soumission"
    assert records[1]["price"] == "£50.10"


def test_export_excel_writes_correct_sheet():
    path = exporter.export_products(SAMPLE_PRODUCTS, "attic", "excel")
    assert path.endswith(".xlsx")

    df = pd.read_excel(path, engine="openpyxl")
    assert len(df) == 2
    assert list(df.columns) == ["name", "price", "rating", "product_url", "image_url", "availability", "category"]


def test_export_with_empty_product_list_returns_empty_string():
    path = exporter.export_products([], "nothing", "csv")
    assert path == ""


def test_export_with_unsupported_format_raises_value_error():
    with pytest.raises(ValueError):
        exporter.export_products(SAMPLE_PRODUCTS, "attic", "xml")


def test_output_filename_sanitizes_special_characters_in_keyword():
    path = exporter.export_products(SAMPLE_PRODUCTS, "sci-fi & fantasy!", "json")
    filename = path.split("/")[-1]
    assert " " not in filename
    assert "&" not in filename
    assert "!" not in filename


def test_output_filename_falls_back_when_keyword_has_no_alphanumeric_chars():
    path = exporter.export_products(SAMPLE_PRODUCTS, "!!!", "json")
    filename = path.split("/")[-1]
    assert filename.startswith("results_")
