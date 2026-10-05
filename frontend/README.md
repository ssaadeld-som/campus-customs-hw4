# Campus Customs frontend

React + Vite + TypeScript storefront for Homework 4.

From the Homework 4 folder, start the API in one terminal:

```bash
source .venv/bin/activate
uvicorn backend.main:app --reload
```

Then start the frontend in a second terminal:

```bash
cd frontend
npm run dev
```

Open the URL printed by Vite (normally `http://localhost:5173`). The frontend expects the local FastAPI service at `http://localhost:8000`; set `VITE_API_URL` if that address changes.

`backend/main.py` reads the provided SQLite catalogue, inventory records, and product images. The chat endpoint is a catalogue-aware temporary interaction for the storefront; it will be replaced with the PydanticAI agent in the later agent task.
