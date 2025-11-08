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
pip install -r requirements.txt
```

### Run frontend and backend together

From the repository root:

```bash
chmod +x ./run.sh
./run.sh
```

The FastAPI server will be available on `http://localhost:8000` and the Next.js app on `http://localhost:3000`.
