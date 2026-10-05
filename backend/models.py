"""Pydantic models shared by the FastAPI routes and Campus Customs agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2_000)
    session_token: str | None = None
    page_context: "PageContext" = Field(default_factory=lambda: PageContext())


class StockNotificationRequest(BaseModel):
    email: str
    product_id: str
    size: str


class PageContext(BaseModel):
    path: str = "/"
    page_title: str = "Home"
    product_id: str | None = None


class CustomerContext(BaseModel):
    user_id: int
    first_name: str | None = None
    last_name: str | None = None
    email: str


class StoredChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    products: list["ProductCard"] = Field(default_factory=list)


@dataclass
class AgentDependencies:
    customer: CustomerContext | None
    page_context: PageContext


class AgentAnswer(BaseModel):
    """Structured reply produced by the shopping agent."""

    model_config = ConfigDict(extra="forbid")
    message: str = Field(description="Helpful, concise answer in the Campus Customs voice.")
    product_ids: list[str] = Field(
        default_factory=list,
        max_length=4,
        description="Relevant catalogue product IDs returned by a tool. Empty when no card is useful.",
    )
    stop_reason: Literal["grounded_answer", "not_found", "safety_decline", "clarification"] = Field(
        default="grounded_answer",
        description="Why the agent ended its bounded turn; not_found is used when tools find no match.",
    )


class SizeStock(BaseModel):
    """A real inventory record for exactly one product size."""

    size: str = Field(description="Size label stored in the inventory table, such as S, M, L, or XL.")
    quantity: int = Field(ge=0, description="Current number of units for this exact size.")
    available: bool = Field(description="True only when quantity is greater than zero.")


class ProductInfoLookup(BaseModel):
    """Database-backed product attributes suitable for an agent answer."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    price: float = Field(ge=0)
    image_url: str


class ProductStockLookup(BaseModel):
    """Database-backed complete size run for a product."""

    product_id: str
    sizes: list[SizeStock]
    total_stock: int = Field(ge=0)


class ProductCard(BaseModel):
    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]
    image_url: str
    price: float
    total_stock: int
    stock_by_size: list[SizeStock]
