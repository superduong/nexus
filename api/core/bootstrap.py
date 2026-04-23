"""Một lần tạo admin mặc định khi DB còn trống (deploy Render / Postgres mới)."""

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select

from api.core.config import get_settings
from api.core.security import hash_password
from api.db.models import User
from api.db.session import SessionLocal

log = logging.getLogger(__name__)


def seed_admin_if_configured() -> None:
    s = get_settings()
    if not s.seed_admin_on_empty_db:
        return
    db = SessionLocal()
    try:
        n = db.scalar(select(func.count()).select_from(User)) or 0
        if n > 0:
            return
        now = datetime.now(timezone.utc)
        db.add(
            User(
                email=s.seed_admin_email,
                username=s.seed_admin_username,
                first_name="",
                last_name="",
                password=hash_password(s.seed_admin_password),
                is_superuser=True,
                is_staff=True,
                is_active=True,
                date_joined=now,
                created_at=now,
            )
        )
        db.commit()
        log.warning(
            "Created initial admin user %s (set SEED_ADMIN_ON_EMPTY_DB=false after first login if you want)",
            s.seed_admin_email,
        )
    except Exception:
        db.rollback()
        log.exception("seed_admin_if_configured failed")
    finally:
        db.close()
