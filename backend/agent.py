"""PydanticAI shopping agent configured for Portkey's OpenAI-compatible gateway."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
try:
    from audit import append_audit
except ModuleNotFoundError:
    from .audit import append_audit

try:
    from models import AgentAnswer, AgentDependencies, CustomerContext, PageContext
    from tools import get_product_info, get_stock_by_size, page_context_for_agent, search_products
except ModuleNotFoundError:  # Supports `from backend.agent import ...` during root-level tests.
    from .models import AgentAnswer, AgentDependencies, CustomerContext, PageContext
    from .tools import get_product_info, get_stock_by_size, page_context_for_agent, search_products

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")
load_dotenv(BACKEND_DIR.parent / ".env")
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
MODEL_NAME = "gpt-5.6-luna"


@lru_cache(maxsize=1)
def build_agent() -> Agent[AgentDependencies, AgentAnswer]:
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the Homework 4 root .env file.")
    provider = OpenAIProvider(base_url="https://api.portkey.ai/v1", api_key=api_key)
    model = OpenAIChatModel(MODEL_NAME, provider=provider)
    shopper = Agent(
        model,
        deps_type=AgentDependencies,
        output_type=AgentAnswer,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        retries=1,
        model_settings={"temperature": 0.2},
    )
    shopper.tool_plain(search_products)
    shopper.tool_plain(get_product_info)
    shopper.tool_plain(get_stock_by_size)
    @shopper.tool
    def get_current_page(ctx: RunContext[AgentDependencies]) -> PageContext:
        """Get the current browser page and optional product ID for this chat turn."""
        return page_context_for_agent(ctx.deps.page_context)
    return shopper


def respond_to_customer(message: str, customer: CustomerContext | None, page_context: PageContext, history: list[str]) -> AgentAnswer:
    """Run one bounded shopping-agent conversation turn."""
    identity = "Guest shopper (no account or email available)." if customer is None else f"Logged-in customer: {customer.first_name or ''} {customer.last_name or ''} ({customer.email})."
    conversation = "\n".join(history[-8:]) or "No earlier saved conversation."
    prompt = f"{identity}\nSaved conversation (oldest to newest):\n{conversation}\n\nCurrent customer message: {message}"
    append_audit("agent.run", message, {"history_items": len(history[-8:]), "page": page_context.path}, "started")
    try:
        result = build_agent().run_sync(prompt, deps=AgentDependencies(customer=customer, page_context=page_context), usage_limits=UsageLimits(request_limit=4))
    except Exception as exc:
        append_audit("agent.run", message, str(exc), f"error:{type(exc).__name__}")
        raise
    answer = result.output
    if answer.stop_reason == "not_found":
        answer = answer.model_copy(update={"message": "Not Found", "product_ids": []})
    append_audit("agent.run", message, {"product_ids": answer.product_ids, "message": answer.message}, answer.stop_reason)
    return answer
