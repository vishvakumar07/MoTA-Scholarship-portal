"""Phase 3 scheme engine schema migration

Revision ID: 0002_phase3_scheme_engine
Revises: 0001_initial_schema
Create Date: 2026-09-25 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models.base import Base
import models  # Ensure all models are registered in Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0002_phase3_scheme_engine"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    pass
