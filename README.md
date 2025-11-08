# dalia

Conversational money assistant

## Development

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+

### Install dependencies

```bash
# Frontend
cd frontend
npm install

# Backend
cd ../backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# deactivate when you're done working on the backend
deactivate
```

### Run frontend and backend together

From the repository root:

```bash
chmod +x ./run.sh
./run.sh
```

The FastAPI server will be available on `http://localhost:8000` and the Next.js app on `http://localhost:3000`.

> `./run.sh` automatically ensures the backend virtual environment at `backend/.venv` exists
> and installs dependencies when `backend/requirements.txt` changes, so you do not need to
> manually activate the environment when using the combined runner.

### Generate React Query hooks

1. Ensure the FastAPI dependencies are installed (`pip install -r backend/requirements.txt`) and the frontend dependencies are installed (`npm install` inside `frontend/`).
2. From inside the `frontend/` directory, run:

   ```bash
   npm run generate:api
   ```

   This will export the FastAPI OpenAPI schema to `frontend/openapi.json` and regenerate the typed React Query hooks inside `frontend/lib/api/` using Orval.
