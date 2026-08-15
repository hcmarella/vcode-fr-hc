"""push sync: add 'pending' to sync_run_status_enum

Split into its own migration on purpose: Postgres forbids using a value added
via ALTER TYPE ... ADD VALUE in the same transaction that added it, and
Alembic runs each migration's upgrade() in one transaction. The rest of the
push-sync schema change (which actually uses 'pending') is the next revision.

Revision ID: 6c567f93b09e
Revises: 56154208ca2d
Create Date: 2026-08-15 20:40:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = '6c567f93b09e'
down_revision: Union[str, None] = '56154208ca2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE sync_run_status_enum ADD VALUE IF NOT EXISTS 'pending'")


def downgrade() -> None:
    # Postgres can't drop a single enum value without recreating the type and
    # remapping every dependent column/row. Not worth the risk for a value
    # with no other side effects if unused; left in place.
    pass
