# Problem 9 usability improvements

## Frontend improvements

### 1. Hover and keyboard product preview

Product cards now lift slightly and enlarge their image on hover, with a “Preview item” cue. The same interaction is available through keyboard focus, with a visible focus outline. This gives shoppers a low-effort way to scan products before committing to a click while keeping the existing detail page one click away.

### 2. Segment-aware size chart

Every product detail page now includes a responsive fit guide for Youth, Women, and Men. It lists standard US casual/activewear measurements in inches for each segment's sizes: chest/bust, waist, and hip. The page explains that the chart is a standard guide and that the product description should take precedence when a garment has a special fit. This reduces uncertainty and helps customers choose sizes without leaving the product page.

Out-of-stock sizes also expose a back-in-stock email form. The customer selects a sold-out size and enters an email; FastAPI validates the product and size, rejects already-available sizes, and stores a deduplicated request in `stock_notifications`.

## Backend improvements

### 1. Bounded and efficient agent workflow

`backend/agent.py` caches the constructed PydanticAI agent, so tool schemas and the Portkey model are not rebuilt for every message. Each run remains bounded by `UsageLimits(request_limit=4)`, the prompt limits searches to one shortlist plus only necessary detail/stock lookups, and it tells the agent to stop when no match is found. The product-card pipeline caps cards at four, preventing runaway tool loops and unnecessary model tokens.

### 2. Item-specific, segment-aware answers and availability opt-in

The agent prompt now directs responses to use the exact product, customer segment, size, color, budget, and availability details present in the question and database tools. It asks one focused clarification only when needed, and never invents a fit, stock count, or notification.

When a size is unavailable, the product page provides the explicit opt-in email workflow. `POST /api/stock-notifications` validates the email, product, and size, writes a unique `(email, product_id, size)` request, and tells the shopper that the request was saved. The notification table is intentionally separate from chat history so a business workflow can later process it without changing conversation records.

## Why this helps Campus Customs

The improvements shorten the path from discovery to a confident purchase, reduce sizing uncertainty and inaccurate stock assumptions, lower agent operating cost, and turn out-of-stock interest into a permission-based customer lead.

## Revision: browse controls and catalogue scale

- The API now adds a consistent `category` (Tops & shirts, Jackets & sweaters, Activewear, or Bottoms) and `customer_segment` (Youth, Men, Women, or Unisex) to each catalogue result. It also returns `available_sizes` and `total_stock` in one catalogue response.
- The Products page filters on category, segment, size, availability, and color before rendering. It paginates the filtered set into 16 products per page in a four-by-four wide-screen grid, reducing cognitive load compared with browsing all 102 products at once.
- The hover preview is retained and strengthened: a card lifts, its high-quality product image zooms, and a clear preview cue appears before the customer clicks through.

## Revision: accurate discovery and measurement clarity

- A submitted chat catalogue search now applies directly to the Products grid. For example, entering `hoodie` and sending it opens (or refreshes) Products with the matching hoodies, retains the normal filters and 16-item pagination, and offers one clear action to remove the chat search.
- Product filtering now searches the catalogue's customer-facing name, garment type, description, stored color values, and search tags. Category and customer-segment choices also use those grounded keywords, so a product is not excluded merely because one derived label is too narrow.
- The fit guide labels every measurement column with `(in.)` and states that all values are body measurements in inches. This makes the reference units explicit for Youth, Women, and Men tables.
