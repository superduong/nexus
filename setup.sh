#!/bin/bash
set -e

echo "=== NEXUS setup (FastAPI) ==="

if [ ! -f .env ]; then
  cp .env.example .env
  echo "✓ .env created from .env.example"
fi

echo "Installing Python packages..."
pip install -r requirements.txt

echo "Applying DB migrations (Alembic)..."
alembic upgrade head

echo "Creating default admin user if missing (admin@nexus.com / admin1234)..."
python << 'PY'
from datetime import datetime, timezone

from sqlalchemy import select

from api.core.security import hash_password
from api.db.models import User
from api.db.session import SessionLocal

db = SessionLocal()
try:
    email = "admin@nexus.com"
    if db.scalar(select(User).where(User.email == email)):
        print("Admin already exists")
    else:
        now = datetime.now(timezone.utc)
        db.add(
            User(
                email=email,
                username="admin",
                first_name="",
                last_name="",
                password=hash_password("admin1234"),
                is_superuser=True,
                is_staff=True,
                is_active=True,
                date_joined=now,
                created_at=now,
            )
        )
        db.commit()
        print("Admin created: admin@nexus.com / admin1234")
finally:
    db.close()
PY

echo ""
echo "=== Done ==="
echo "  uvicorn api.main:app --reload --host 0.0.0.0 --port 8000"
echo "  docker compose up"
echo ""
echo "  Terminal: http://localhost:8000/"
echo "  Login page: http://localhost:8000/login/"
echo "  API docs: http://localhost:8000/docs"
