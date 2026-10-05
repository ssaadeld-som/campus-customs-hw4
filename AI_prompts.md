# AI Prompts

## Problem 1: Vibe coder prompts

### Initial prompt

Today I am starting Homework 4. Please create this `AI_prompts.md` file, set up the Homework 4 folder, and download the course data ZIP so I can begin the assignment.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 2: Analyze the database

### Initial prompt

Analyze the Homework 4 database. Record each table and its fields in `output/harness.md`, and briefly explain why every field matters to the Campus Customs shop or chatbot.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 3: Build the Campus Customs website

### Initial prompt

Scaffold a React, Vite, and TypeScript storefront for Campus Customs. I want a top navigation bar with Home, Products, About Us, Log In, and Create Account. Build a navy-and-white collegiate storefront in an original voice, use every catalogue image on the Products page, add individual product pages with size and stock details, and include a floating chat panel connected to a FastAPI backend in `backend/main.py`.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 4: Create account and login

### Initial prompt

Make the Log In and Create Account pages functional. The login form needs email and password fields plus a Create Account link. Registration needs first name, last name, email, password, confirm password, and an Enter button. Show errors for missing fields or mismatched passwords, save a successful registration in the users table with a securely hashed password, and test a database account using the requested password without exposing it in the UI or source code.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 5: PydanticAI agent backend

### Initial prompt

Build a PydanticAI shopping agent behind FastAPI. Put the agent, tools, models, and Campus Customs voice and safety prompt in separate backend files. The chatbot should answer customer messages with grounded product cards, and the backend must run from the backend folder with `uvicorn main:app --reload --port 8000`.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 6: Tools: product info and stock

### Initial prompt

Update the Campus Customs agent so it uses typed database tools for real product descriptions, prices, and stock by every size. Do not let the agent invent product information. Update the agent prompt, tool return models, and harness explanation of the lookup fields and why each one is included.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 7: Chat search that updates the page

### Initial prompt

Make chat searches update the main Campus Customs page with the matching product cards returned by the agent. Those cards should show normal product information and link to the existing Problem 3 detail page with the enlarged image, description, price, sizes, and stock. Update the agent prompt and harness to explain the flow.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 8: Customer memory

### Initial prompt

Add customer memory for signed-in users only: save and retrieve their chat history from the database, pass their name and email to the agent, and let guests chat without saving memory. Also pass the current page as agent tool context so the agent can answer questions about the page the customer is viewing. Document storage, customer fields, and page context in the harness.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 9: Usability improvements

### Initial prompt

Add two frontend usability improvements: hover/focus product previews and a Youth/Women/Men size chart with standard measurements. Add two backend improvements: keep model workflows bounded and token-efficient, and tailor answers to the exact product, segment, size, color, and availability. When a size is unavailable, let the customer opt in to an email notification. Document all four improvements in `output/usability.md`.

### Follow-up prompt

No follow-up prompt was needed for this problem.

## Problem 10: Style the website

### Initial prompt

Improve the Campus Customs visual design around clear typography, professional and consistent product cards, responsive use of the canvas, high-quality product presentation, and sticky navigation. Keep links and buttons working across pages and document the concise design rationale in `output/design.md`.

### Follow-up prompt

Use one font throughout the site, make navigation and product-detail size labels easier to read, and revise Product browsing to use category, customer segment, size, availability, and color filters. Categorize API product results, paginate filtered results at 16 items per page in a four-by-four desktop grid, and retain a stronger zoomed product preview on hover.

### Latest revision prompt

Make chat product searches update the actual Products grid as soon as the shopper presses Enter (for example, `hoodie`), instead of showing a separate set of cards. Match the catalogue filters against real product names, descriptions, tags, colors, and segment wording. Add explicit measurement units to every size-chart column, and make the navy-and-white university store feel warmer and more cheerful without losing a professional shopping experience.

## Problem 11: Site testing (app check)

### Initial prompt

Start the local website for feature testing. Prepare a grader-friendly `output/app_check.html` that links relatively to three screenshots in `output/app_check_images`: an inventory chat lookup, dynamic search cards, and a usability feature such as the size chart. Include a short caption for each check.

### Follow-up prompt

The supplied inventory-lookup screenshot belongs at `output/app_check_images/inventory.png`. Dynamic-search validation should confirm that chat results update the normal Products grid, and size-chart validation should confirm that all measurement units are visible.
