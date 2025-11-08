## dalia backend

This FastAPI backend provides the server-side capabilities for the frontend.

### Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run the development server

```bash
uvicorn app.main:app --reload --port 8000
```
