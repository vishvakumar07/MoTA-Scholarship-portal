"""Phase 7 government integration verification schema migration.

Revision ID: 0003_phase7_gov_verification
Revises: 0002_phase3_scheme_engine
Create Date: 2026-09-25 11:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from models.base import Base
import models  # Ensure all models are registered in Base.metadata

# revision identifiers, used by Alembic.
revision: str = "0003_phase7_gov_verification"
down_revision: Union[str, None] = "0002_phase3_scheme_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    # Drop only the Phase 7 tables
    op.execute("DROP TABLE IF EXISTS government_verification_attempts CASCADE")
    op.execute("DROP TABLE IF EXISTS government_verifications CASCADE")
    op.execute("DROP TYPE IF EXISTS gov_integration_name_enum")
    op.execute("DROP TYPE IF EXISTS gov_verification_status_enum")
