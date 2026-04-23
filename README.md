# NEXUS — Unified Trading Terminal

FastAPI backend with a browser trading terminal UI, inspired by TealStreet.

## Stack

- **FastAPI** + Uvicorn (HTTP + WebSocket)
- **SQLAlchemy 2** + **Alembic** (migrations)
- **JWT** (python-jose) + passlib (`pbkdf2_sha256` compatible with legacy Django password hashes)
- **Celery** + Redis (background jobs)
- **CCXT** (Binance, OKX, …)
- **SQLite** (dev) / PostgreSQL (prod)

## Quick start (local)

```bash
cd nexus
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
bash setup.sh
# Redis must be running for cache + Celery
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/login/ — default admin (after `setup.sh`): `admin@nexus.com` / `admin1234`.

API docs: http://localhost:8000/docs

## Docker

```bash
docker compose up --build
```

## Layout

```
nexus/
├── api/                 # FastAPI app, routers, DB models, services
├── workers/             # Celery app + tasks + beat schedule
├── alembic/             # DB migrations
├── templates/terminal/  # Terminal HTML
├── static/              # Static assets (/static)
├── setup.sh
└── docker-compose.yml
```

## Database

```bash
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

Existing databases created with Django remain compatible with the same table names.

## Production

Set in `.env`:

```env
DEBUG=False
DATABASE_URL=postgresql://user:pass@host:5432/nexus_db
SECRET_KEY=random-long-secret
CORS_ALLOWED_ORIGINS=https://your-frontend.example
```
