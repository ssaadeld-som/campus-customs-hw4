"""Campus Customs API for the Vite storefront.

Run from the Homework 4 folder with:
    .venv/bin/uvicorn backend.main:app --reload
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import sqlite3
import time
from pathlib import Path

import bcrypt
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
try:
    from agent import respond_to_customer
    from models import ChatRequest, CustomerContext, StockNotificationRequest, StoredChatMessage
    from tools import product_cards
except ModuleNotFoundError:  # Supports `uvicorn backend.main:app` from the homework root.
    from .agent import respond_to_customer
    from .models import ChatRequest, CustomerContext, StockNotificationRequest, StoredChatMessage
    from .tools import product_cards

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "campus_customs.db"
PRODUCT_IMAGE_DIR = PROJECT_ROOT / "data" / "products"

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.mount("/media/products", StaticFiles(directory=PRODUCT_IMAGE_DIR), name="products")


@app.on_event("startup")
def ensure_notification_table() -> None:
    with database_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS stock_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                product_id TEXT NOT NULL,
                size TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(email, product_id, size)
            )
        """)
        connection.commit()


class RegisterRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str
    confirm_password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def database_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _encode(payload: dict[str, object]) -> str:
    return base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")


def _decode(value: str) -> dict[str, object]:
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def issue_session_token(user_id: int) -> str:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the Homework 4 root .env file.")
    payload = _encode({"user_id": user_id, "expires_at": int(time.time()) + 86_400})
    signature = hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def customer_from_token(token: str | None) -> CustomerContext | None:
    if not token or "." not in token:
        return None
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        return None
    payload, signature = token.rsplit(".", 1)
    expected = hmac.new(key.encode(), payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        claims = _decode(payload)
        if int(claims["expires_at"]) < time.time():
            return None
        user_id = int(claims["user_id"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    with database_connection() as connection:
        user = connection.execute("SELECT id, first_name, last_name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    return CustomerContext(user_id=user["id"], first_name=user["first_name"], last_name=user["last_name"], email=user["email"]) if user else None


def save_chat_message(user_id: int, role: str, content: str, products: list[dict[str, object]] | None = None) -> None:
    with database_connection() as connection:
        connection.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, json.dumps(products) if products else None),
        )
        connection.commit()


def chat_history(user_id: int) -> list[StoredChatMessage]:
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY created_at, id", (user_id,)
        ).fetchall()
    return [StoredChatMessage(role=row["role"], content=row["content"], products=json.loads(row["products_json"]) if row["products_json"] else []) for row in rows]


def normalized_email(email: str) -> str:
    value = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
        raise HTTPException(status_code=400, detail="Enter a valid email address.")
    return value


def required_text(value: str, label: str) -> str:
    value = value.strip()
    if not value:
        raise HTTPException(status_code=400, detail=f"{label} is required.")
    return value


def password_hash(password: str) -> str:
    """Create a salted bcrypt hash; the plaintext password is never persisted."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def password_matches(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Older classroom records may use another hash format. Do not accept them blindly.
        return False


def product_from_row(row: sqlite3.Row) -> dict[str, object]:
    product = dict(row)
    product["colors"] = json.loads(product["colors"])
    product["search_tags"] = json.loads(product["search_tags"])
    product["image_url"] = f"/media/{product['image_file_path']}"
    product["category"] = product_category(product)
    product["customer_segment"] = customer_segment(product)
    return product


def product_category(product: dict[str, object]) -> str:
    """Classify from the same customer-facing fields used by catalogue filters."""
    text = f"{product['name']} {product['garment_type']} {product['description']} {' '.join(product['colors'])} {' '.join(product['search_tags'])}".lower()
    if any(term in text for term in ("pant", "shorts", "legging", "jogger")):
        return "Bottoms"
    if any(term in text for term in ("baseball", "soccer", "hockey", "crew", "fencing", "sailing", "diving", "volleyball", "tennis", "track", "golf", "sports")):
        return "Activewear"
    if "t-shirt" in text or "t shirt" in text or "long sleeve" in text:
        return "Tops & shirts"
    return "Jackets & sweaters"


def customer_segment(product: dict[str, object]) -> str:
    """Return a segment only when the real catalogue wording identifies one."""
    text = f"{product['name']} {product['garment_type']} {product['description']} {' '.join(product['search_tags'])}".lower()
    if any(term in text for term in ("youth", "kids", "child")):
        return "Youth"
    if any(term in text for term in ("women", "woman", "mom", "grandma", "aunt")):
        return "Women"
    if any(term in text for term in ("men", "mens", "dad", "grandpa", "uncle", "brother")):
        return "Men"
    return "Unisex"


def inventory_for_product(connection: sqlite3.Connection, product_id: str) -> list[dict[str, object]]:
    rows = connection.execute(
        "SELECT size, quantity FROM inventory WHERE product_id = ? ORDER BY id", (product_id,)
    ).fetchall()
    return [dict(row) for row in rows]


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/products")
def list_products() -> list[dict[str, object]]:
    with database_connection() as connection:
        rows = connection.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inventory_rows = connection.execute("SELECT product_id, size, quantity FROM inventory").fetchall()
    inventory: dict[str, list[dict[str, object]]] = {}
    for item in inventory_rows:
        inventory.setdefault(item["product_id"], []).append(dict(item))
    products = []
    for row in rows:
        product = product_from_row(row)
        stock = inventory.get(str(product["product_id"]), [])
        product["available_sizes"] = [item["size"] for item in stock if item["quantity"] > 0]
        product["total_stock"] = sum(item["quantity"] for item in stock)
        products.append(product)
    return products


@app.get("/api/products/{product_id}")
def get_product(product_id: str) -> dict[str, object]:
    with database_connection() as connection:
        row = connection.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = product_from_row(row)
        inventory = inventory_for_product(connection, product_id)
    product["inventory"] = inventory
    product["total_stock"] = sum(item["quantity"] for item in inventory)
    return product


@app.post("/api/stock-notifications", status_code=201)
def stock_notification(request: StockNotificationRequest) -> dict[str, str]:
    email = normalized_email(request.email)
    size = required_text(request.size, "Size")
    with database_connection() as connection:
        product = connection.execute("SELECT 1 FROM catalogue WHERE product_id = ?", (request.product_id,)).fetchone()
        stock = connection.execute(
            "SELECT quantity FROM inventory WHERE product_id = ? AND lower(size) = lower(?)",
            (request.product_id, size),
        ).fetchone()
        if product is None or stock is None:
            raise HTTPException(status_code=404, detail="That product size could not be found.")
        if stock["quantity"] > 0:
            raise HTTPException(status_code=409, detail="That size is already available.")
        connection.execute(
            "INSERT OR IGNORE INTO stock_notifications (email, product_id, size) VALUES (?, ?, ?)",
            (email, request.product_id, size),
        )
        connection.commit()
    return {"message": f"We will email {email} when size {size} is available again."}


@app.post("/api/auth/register", status_code=201)
def register(request: RegisterRequest) -> dict[str, object]:
    first_name = required_text(request.first_name, "First name")
    last_name = required_text(request.last_name, "Last name")
    email = normalized_email(request.email)
    if not request.password:
        raise HTTPException(status_code=400, detail="Password is required.")
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match.")

    with database_connection() as connection:
        existing_user = connection.execute(
            "SELECT id FROM users WHERE lower(email) = ?", (email,)
        ).fetchone()
        if existing_user:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        cursor = connection.execute(
            """
            INSERT INTO users (name, email, password_hash, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"{first_name} {last_name}", email, password_hash(request.password), first_name, last_name),
        )
        user_id = cursor.lastrowid
        connection.commit()
    return {"message": "Account created. You can now log in.", "user": {"id": user_id, "email": email, "first_name": first_name}}


@app.post("/api/auth/login")
def login(request: LoginRequest) -> dict[str, object]:
    email = normalized_email(request.email)
    if not request.password:
        raise HTTPException(status_code=400, detail="Password is required.")
    with database_connection() as connection:
        user = connection.execute(
            "SELECT id, email, first_name, password_hash FROM users WHERE lower(email) = ?", (email,)
        ).fetchone()
    if user is None or not password_matches(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"message": f"Welcome back, {user['first_name'] or 'Campus Customs customer'}!", "user": {"id": user["id"], "email": user["email"], "first_name": user["first_name"]}, "session_token": issue_session_token(user["id"])}


@app.get("/api/chat/history")
def get_chat_history(authorization: str | None = Header(default=None)) -> dict[str, object]:
    token = authorization.removeprefix("Bearer ") if authorization else None
    customer = customer_from_token(token)
    if customer is None:
        raise HTTPException(status_code=401, detail="Sign in to retrieve chat history.")
    return {"messages": [message.model_dump() for message in chat_history(customer.user_id)]}


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    query = request.message.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Please enter a message.")
    customer = customer_from_token(request.session_token)
    history = chat_history(customer.user_id) if customer else []
    if customer:
        save_chat_message(customer.user_id, "user", query)
    try:
        answer = respond_to_customer(query, customer, request.page_context, [f"{item.role}: {item.content}" for item in history])
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail="The shopping assistant is temporarily unavailable.") from exc
    products = [card.model_dump() for card in product_cards(answer.product_ids)]
    if customer:
        save_chat_message(customer.user_id, "assistant", answer.message, products)
    return {"message": answer.message, "products": products, "customer": customer.model_dump() if customer else None}
