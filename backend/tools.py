"""Read-only SQLite tools used by the Campus Customs shopping agent."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

try:
    from models import PageContext, ProductCard, ProductInfoLookup, ProductStockLookup, SizeStock
    from audit import audited_tool
except ModuleNotFoundError:  # Supports `from backend.tools import ...` during root-level tests.
    from .models import PageContext, ProductCard, ProductInfoLookup, ProductStockLookup, SizeStock
    from .audit import audited_tool

ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = ROOT / "data" / "campus_customs.db"


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _product(row: sqlite3.Row, include_inventory: bool = False) -> dict[str, object]:
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    product["image_url"] = f"/media/{product['image_file_path']}"
    with _connection() as connection:
        inventory = [dict(item) for item in connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product["product_id"],)
        )]
    product["total_stock"] = sum(item["quantity"] for item in inventory)
    if include_inventory:
        product["inventory"] = inventory
    return product


def _stock(product_id: str) -> ProductStockLookup:
    with _connection() as connection:
        rows = connection.execute(
            "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)
        ).fetchall()
    sizes = [SizeStock(size=row["size"], quantity=row["quantity"], available=row["quantity"] > 0) for row in rows]
    return ProductStockLookup(product_id=product_id, sizes=sizes, total_stock=sum(item.quantity for item in sizes))


@audited_tool("search_products")
def search_products(query: str, garment_type: str = "", color: str = "", max_price: float = 0) -> list[ProductCard]:
    """Search the Campus Customs catalogue by customer words, garment type, color, or budget.

    Call this before recommending a product or stating a price. The result provides valid
    product IDs that may be returned in `product_ids`.
    """
    terms = [term.lower() for term in (query + " " + garment_type + " " + color).split() if term]
    with _connection() as connection:
        rows = connection.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
    matches = []
    for row in rows:
        product = _product(row)
        haystack = " ".join([
            str(product["name"]), str(product["garment_type"]), str(product["description"]),
            " ".join(product["colors"]), " ".join(product["search_tags"]),
        ]).lower()
        if terms and not any(term in haystack for term in terms):
            continue
        if max_price and float(product["price"]) > max_price:
            continue
        matches.append(product)
    return [
        ProductCard.model_validate({**product, "stock_by_size": _stock(str(product["product_id"])).sizes})
        for product in matches[:12]
    ]


@audited_tool("get_product_info")
def get_product_info(product_id: str) -> ProductInfoLookup:
    """Look up the authoritative description, price, colors, and image for one real catalogue product."""
    with _connection() as connection:
        row = connection.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        raise ValueError("No product exists with that product_id.")
    product = _product(row)
    return ProductInfoLookup.model_validate(product)


@audited_tool("get_stock_by_size")
def get_stock_by_size(product_id: str) -> ProductStockLookup:
    """Look up current stock for every size of a real product. Do not guess availability or quantity."""
    with _connection() as connection:
        exists = connection.execute("SELECT 1 FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
    if exists is None:
        raise ValueError("No product exists with that product_id.")
    return _stock(product_id)


def product_cards(product_ids: list[str]) -> list[ProductCard]:
    """Return safe, UI-ready cards only for real product IDs selected by the agent."""
    cards: list[ProductCard] = []
    for product_id in dict.fromkeys(product_ids):
        if len(cards) == 4:
            break
        try:
            info = get_product_info(product_id)
            stock = get_stock_by_size(product_id)
        except ValueError:
            continue
        cards.append(ProductCard.model_validate({**info.model_dump(), "total_stock": stock.total_stock, "stock_by_size": stock.sizes}))
    return cards


@audited_tool("get_current_page")
def page_context_for_agent(context: PageContext) -> PageContext:
    """Return the browser page supplied by the trusted frontend for the current chat turn."""
    return context
