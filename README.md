# relayworks-ai

## Local demo reset

Use the reset script when you want a clean, understandable dashboard state before demos or testing.

```bash
cd backend
source .venv/bin/activate
python scripts/reset_demo_data.py --confirm-reset
```

The script only overwrites local JSON files under `backend/data/` when `--confirm-reset` is present. Before writing new data, it creates a timestamped backup folder at:

```text
backend/data/backups/demo_reset_<timestamp>/
```

## Run the backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run the frontend

```bash
cd frontend
npm run dev
```
