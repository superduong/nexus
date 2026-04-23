"""Create all tables from SQLAlchemy models (fresh DB or checkfirst).

Revision ID: 0001
Revises:
Create Date: 2026-04-23

"""

from typing import Sequence, Union

from alembic import op

from api.db.models import Base

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind, checkfirst=True)
