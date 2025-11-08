## dalia backend

This FastAPI backend provides the server-side capabilities for the frontend.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# optional: keep dependencies fresh
# pip install --upgrade pip
```

### Run the development server

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

If you prefer not to manage the environment manually, run the repository-level `./run.sh`
from the project root. It creates/updates `backend/.venv` automatically and starts both
the FastAPI backend and the Next.js frontend.
