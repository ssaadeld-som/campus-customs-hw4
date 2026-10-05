# Homework 4 database observations

Source inspected: `data/campus_customs.db` (SQLite). The database currently contains 102 catalogue products, 612 size-level inventory records, 3 users, and 22 chat messages.

## `catalogue`

This is the product master table. `product_id` is its primary key; it is the identifier used to connect a product to inventory.

| Field | Type | Why it matters |
| --- | --- | --- |
| `product_id` | TEXT, primary key | Gives every product a stable identifier for lookups, inventory joins, product cards, and chatbot recommendations. |
| `name` | TEXT, required | Supplies the customer-facing product name and a simple term the chatbot can search or mention. |
| `garment_type` | TEXT, required | Lets the site and chatbot distinguish items such as hoodies, T-shirts, and crewnecks for browsing and filtering. |
| `description` | TEXT, required | Provides the detail needed for product pages and useful natural-language answers about a garment. |
| `colors` | TEXT, required | Stores a JSON-style list of color options for color-based search and product presentation. |
| `search_tags` | TEXT, required | Stores a JSON-style list of searchable concepts (for example, sport, school, or style) that help the chatbot match a customer request to products. |
| `image_file_path` | TEXT, required | Maps the catalogue item to its local product image so the UI can render a product card or detail page. |
| `price` | REAL, required | Provides the price displayed to shoppers and lets the chatbot give accurate price information. |

## `inventory`

This table tracks stock at the individual product-and-size level. Its `product_id` has a declared foreign-key relationship to `catalogue.product_id`.

| Field | Type | Why it matters |
| --- | --- | --- |
| `id` | INTEGER, primary key | Uniquely identifies each inventory row, which is useful for updating or auditing a specific size record. |
| `product_id` | TEXT, required | Connects the stock record to its product so the site can show the right availability beside each item. |
| `size` | TEXT, required | Identifies the size a shopper wants, allowing the site and chatbot to answer size-specific availability questions. |
| `quantity` | INTEGER, required | Holds the current unit count; it drives in-stock/out-of-stock messaging and prevents inaccurate chatbot claims. |

## `users`

This table stores customer accounts. The authentication-related value is retained only as a hash; no password values were inspected or recorded.

| Field | Type | Why it matters |
| --- | --- | --- |
| `id` | INTEGER, primary key | Uniquely identifies a customer and links that customer to their chat history. |
| `name` | TEXT, required | Appears to be a full/display-name field that supports a friendly customer-facing identity. |
| `email` | TEXT, required | Identifies the account for sign-in and account communication. |
| `password_hash` | TEXT, required | Stores a one-way password hash for authentication without saving a plaintext password. |
| `created_at` | TEXT, required; defaults to `datetime('now')` | Records when the account was created for account management and auditing. |
| `first_name` | TEXT, optional | Supports a personalized greeting and the assignment's separate first-name account input. |
| `last_name` | TEXT, optional | Completes the customer's name for account records and the assignment's separate last-name account input. |

## `chat_messages`

This table persists conversation history. Its `user_id` has a declared foreign-key relationship to `users.id`; assistant messages can also save product-card data as JSON.

| Field | Type | Why it matters |
| --- | --- | --- |
| `id` | INTEGER, primary key | Gives each message a stable record for ordering, retrieval, and auditing. |
| `user_id` | INTEGER, required | Associates the message with the signed-in customer so each person sees their own chat history. |
| `role` | TEXT, required | Marks whether content came from the `user` or `assistant`, which is necessary to reconstruct a readable conversation. |
| `content` | TEXT, required | Stores the actual question or chatbot answer shown in the chat interface. |
| `products_json` | TEXT, optional | Stores structured product recommendations attached to an answer so product cards can be restored with the chat history. |
| `created_at` | TEXT, required; defaults to `datetime('now')` | Captures the message time so history can be displayed in conversation order and audited. |

## Relationship and implementation notes

- A catalogue product can have multiple inventory rows, normally one for each size.
- A user can have multiple chat-message rows.
- The `colors`, `search_tags`, and `products_json` columns are TEXT fields containing JSON-style data, so application code should parse them before using them as lists or product-card objects.
- SQLite declares foreign keys for `inventory.product_id` and `chat_messages.user_id`; the application should enable foreign-key enforcement on each connection with `PRAGMA foreign_keys = ON`.

## Authorization and password protection

- The Create Account card sends `first_name`, `last_name`, `email`, `password`, and `confirm_password` to `POST /api/auth/register`. The frontend checks that the two password entries match before sending; the API repeats this validation so a direct API request cannot bypass it.
- The API trims required names, validates the email shape, rejects empty passwords, and checks for an existing email case-insensitively before it inserts a record in `users`.
- A successful registration stores the full name, normalized email, first and last names, and a bcrypt password hash. Bcrypt creates a random salt and applies a deliberately expensive one-way hash; the plaintext password is never stored in the database or sent back in an API response. Hashing—not encryption—is appropriate here because the application only needs to verify a password, never recover it.
- The Log In card sends only the email and password to `POST /api/auth/login`. The API finds the email and uses bcrypt's constant-time password verification. It returns a generic `Incorrect email or password` message for either an unknown email or wrong password, which avoids disclosing whether an account exists.
- Password hashes are excluded from all JSON responses and from this harness. The test account created for Problem 4 is a local database record; its requested test password was used only during verification and is not recorded here.

## Frontend, FastAPI, and PydanticAI agent flow

1. The floating React chat drawer in `frontend/src/App.tsx` sends the typed message as JSON to `POST http://localhost:8000/api/chat`. It displays the returned assistant message and turns the returned product-card objects into links to the matching product pages.
2. `backend/main.py` validates the request with `ChatRequest`, calls `respond_to_customer()` from `agent.py`, and maps the agent's selected product IDs to safe UI cards with `product_cards()` from `tools.py`. The browser receives only the answer text and card fields—not database connection details, secrets, or password hashes.
3. `backend/agent.py` loads `PORTKEY_API_KEY` from the Homework 4 root `.env` at runtime, configures the required `gpt-5.6-luna` model through Portkey's OpenAI-compatible endpoint, loads `prompts/prompt.md`, and registers the catalogue tools. The key is neither hard-coded nor returned by the API.
4. `backend/tools.py` provides read-only SQLite tools: `search_products`, `get_product_details`, and `lookup_stock`. The prompt requires the agent to use these tools before it recommends a product or states price/stock information.
5. `backend/models.py` defines the request and structured `AgentAnswer` contract. The agent's `product_ids` are capped at four and are resolved against the actual catalogue before cards are returned, so invented product IDs cannot render in the UI.

Run the backend from its own folder:

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

The live endpoint test asked for a Yale hoodie under $70. It returned grounded text and two catalogue cards, confirming the FastAPI route, Portkey-backed PydanticAI agent, tool calls, and frontend response shape work together.

## Problem 6: typed product-information and stock tools

The agent has two dedicated, read-only tools in `backend/tools.py`. Both query `campus_customs.db` directly and return Pydantic types defined in `backend/models.py`; neither accepts or uses user-supplied product facts.

| Tool | Return model | Field | Why the field is selected |
| --- | --- | --- | --- |
| `get_product_info(product_id)` | `ProductInfoLookup` | `product_id` | Identifies the exact catalogue row and lets the agent attach only a real product card. |
|  |  | `name` | Gives the customer the database's official product name. |
|  |  | `garment_type` | States what the garment is without the agent inferring it from a name. |
|  |  | `description` | Supplies the database-authored product description requested by the customer. |
|  |  | `colors` | Provides the catalogue's stored color list. |
|  |  | `price` | Provides the exact numeric catalogue price; it is not estimated or reformatted by the tool. |
|  |  | `image_url` | Lets the returned product card point to the corresponding local product image. |
| `get_stock_by_size(product_id)` | `ProductStockLookup` | `product_id` | Links the inventory lookup to the same real catalogue product. |
|  |  | `sizes` | Retains every inventory row for the product, rather than collapsing availability into a vague yes/no answer. |
|  | `SizeStock` within `sizes` | `size` | Preserves the actual size label stored in the database. |
|  |  | `quantity` | Gives the exact number of units for that size. |
|  |  | `available` | A derived boolean (`quantity > 0`) that makes in-stock status unambiguous without changing the stored quantity. |
|  | `ProductStockLookup` | `total_stock` | Sums the returned size quantities to give an honest product-level availability summary. |

`ProductCard` now includes `stock_by_size` and `total_stock`, built from the same `ProductStockLookup` result. The prompt directs the agent to call `get_product_info` whenever description or price is requested and `get_stock_by_size` whenever a customer asks about availability or quantity. This ensures product facts in agent text and cards are traceable to the database.

## Problem 7: chat search updates the page

1. A customer types a product search into the floating chat drawer. `ChatPanel` sends it to the existing `POST /api/chat` endpoint.
2. The agent calls `search_products`, returns verified `product_ids`, and FastAPI resolves those IDs with `product_cards()` before responding. This keeps page results limited to real database products.
3. On a successful reply, `ChatPanel` passes the returned cards and the original search phrase to `App`. `App` stores them in `chatProducts` and `chatQuery`, which causes the page-level `ChatSearchResults` section to render directly under the navigation.
4. Each dynamic result card contains the database-backed product image, name, price, and description. Its image and `View item` link both navigate to `/products/{product_id}`.
5. The existing `ProductDetail` route is reused rather than duplicated. It loads the selected product from FastAPI and presents the enlarged image on the left with description, price, colors, all sizes, and stock quantities on the right. The Clear results control removes only the dynamic search section.

## Problem 8: customer memory and page context

- A successful login returns a signed, 24-hour session token. The browser stores this token with the safe account display fields (`id`, `first_name`, and `email`) in local storage; it never stores a password or password hash.
- Each chat request sends the token. FastAPI verifies its HMAC signature and expiry using a server-side key, then reads the customer record from `users`. The browser does not choose the database user ID used for storage.
- For a verified account, `main.py` saves a `user` row and then an `assistant` row in `chat_messages`. Each row contains `user_id`, `role`, `content`, timestamp, and optional `products_json` for the returned product cards. `GET /api/chat/history` requires the same signed token and returns only that user's rows in chronological order.
- Guests send no session token. They receive a normal agent response, but no `chat_messages` rows are read or written, so they have no persistent memory.
- The agent receives only the logged-in customer's `first_name`, `last_name`, and `email`, plus the most recent saved message text. It does not receive passwords, hashes, payment data, or other users' records. The prompt says not to repeat the email unless explicitly asked.
- For every chat turn, React sends typed `PageContext`: `path`, a human-readable `page_title`, and (on a product detail route) `product_id`. The PydanticAI `get_current_page` tool retrieves that context from the current run dependencies. When a customer asks about “this item” or “this page,” the prompt requires the agent to call this tool and then use database tools for the current facts.

## Problem 12: audit trail, safety, and finish criteria

### End-to-end system contract

- The floating React chat panel sends a bounded `ChatRequest` to `POST /api/chat`. FastAPI resolves the optional signed customer session, supplies recent memory and typed `PageContext`, and calls the cached PydanticAI agent.
- `backend/agent.py` loads `gpt-5.6-luna` through Portkey using `PORTKEY_API_KEY` from the root `.env`; the key is never hard-coded, logged, or returned. The agent uses the instructions in `backend/prompts/prompt.md` and the structured `AgentAnswer` model from `backend/models.py`.
- The read-only tools are `search_products` (catalogue shortlist), `get_product_info` (authoritative name, garment type, description, colors, price, and image URL), `get_stock_by_size` (every stored size and exact quantity), and `get_current_page` (trusted frontend path/title/product context). Tool results are typed with Pydantic models before they can become chat text or cards.
- FastAPI resolves at most four returned product IDs through `product_cards()` and sends only safe UI fields to the browser. The frontend applies search results to the Products grid; product detail links load the authoritative record again.

### Persistent audit trail

- `output/audit_trail.json` is a JSON array of event objects. Every event contains `time` (UTC ISO-8601), `tool_name`, `short_arg`, `short_result`, and `stop_reason`.
- `backend/audit.py` appends events under a process lock and reads existing entries before adding the next one. It does not clear the file between server runs. Arguments/results are truncated and sensitive keys such as passwords, password hashes, API keys, and session tokens are excluded.
- A turn records `agent.run` start and completion/error events. Each database/page tool records its return, `not_found`, or error outcome. This makes the loop and its stopping decision reviewable without storing the full prompt or customer secrets.
- `not_found` is a terminal outcome. The assistant must return the exact phrase `Not Found` when no database match exists and stop instead of retrying or inventing a result.

### Safety and grounding rules

- Merchandise truth comes only from the SQLite catalogue and inventory tables through the typed tools. The agent must not invent prices, stock counts, colors, sizes, products, discounts, customer records, or product images.
- Existing local catalogue image URLs may be displayed, but the agent never generates, recreates, downloads, or claims ownership of new images; source/copyright information remains respected.
- The assistant is read-only for products and accounts. It does not expose passwords, hashes, API keys, payment information, database internals, or another customer's data, and it redirects unsafe or unrelated requests.
- Saved chat history is context, not product truth; current price/description/stock must be looked up again. Guests can chat but do not create history rows.

### Efficiency and run specifications

- Model request limit: `UsageLimits(request_limit=4)` per chat turn; agent construction is cached once per process; retries are limited to one.
- Search results are capped at 12 shortlist records, selected UI cards at four, recent memory at eight messages, and assistant responses at one to four short sentences.
- The loop ends after a grounded answer, a focused clarification, a safety decline, or `Not Found`. No endless retry or tool loop is permitted.
- Run backend from `Hmwrk 4/backend` with `../.venv/bin/uvicorn main:app --reload --port 8000`. Run frontend from `Hmwrk 4/frontend` with `npm run dev -- --host 127.0.0.1`; the current test URL is `http://127.0.0.1:5174`.
- Verification: `./.venv/bin/python -m compileall -q backend`, `cd frontend && npm run lint`, and `npm run build`. The audit file can be reviewed after a chat turn with `output/audit_trail.json`; it must grow cumulatively rather than reset.
