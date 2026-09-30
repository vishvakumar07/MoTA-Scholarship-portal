"""Initial schema migration

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models.base import Base
import models  # Ensure all models are registered in Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables defined in SQLAlchemy ORM models
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Drop all tables defined in SQLAlchemy ORM models
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
