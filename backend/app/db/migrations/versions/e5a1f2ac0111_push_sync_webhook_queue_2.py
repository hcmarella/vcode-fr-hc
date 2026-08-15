"""push sync: webhook + queue support on sync_runs

Revision ID: e5a1f2ac0111
Revises: 6c567f93b09e
Create Date: 2026-08-15 20:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5a1f2ac0111'
down_revision: Union[str, None] = '6c567f93b09e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE sync_trigger_enum AS ENUM ('manual', 'webhook')")
    op.add_column(
        'sync_runs',
        sa.Column(
            'trigger',
            sa.Enum('manual', 'webhook', name='sync_trigger_enum'),
            nullable=False,
            server_default='manual',
        ),
    )
    op.alter_column('sync_runs', 'trigger', server_default=None)

    # started_at now means "worker began executing", set only once a run is
    # claimed -- PENDING rows have no started_at yet.
    op.alter_column('sync_runs', 'started_at', nullable=True)

    op.add_column(
        'sync_runs', sa.Column('requested_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.execute("UPDATE sync_runs SET requested_at = started_at WHERE requested_at IS NULL")
    op.alter_column('sync_runs', 'requested_at', nullable=False)

    op.add_column('sync_runs', sa.Column('source', sa.String(), nullable=True))
    op.add_column('sync_runs', sa.Column('ref', sa.String(), nullable=True))
    # Best-effort backfill for any pre-existing rows: source_ref was built as
    # "source@ref" (or just "source" with no ref). This is lossy for SSH URLs
    # containing '@' themselves, but only affects historical rows from before
    # this migration -- new rows always populate source/ref directly.
    op.execute(
        """
        UPDATE sync_runs
        SET source = split_part(source_ref, '@', 1),
            ref = NULLIF(split_part(source_ref, '@', 2), '')
        WHERE source IS NULL
        """
    )
    op.alter_column('sync_runs', 'source', nullable=False)

    # Debounce constraint: at most one pending/running run per source+ref.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_sync_runs_active_source_ref
        ON sync_runs (source, COALESCE(ref, ''))
        WHERE status IN ('pending', 'running')
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_sync_runs_active_source_ref")
    op.drop_column('sync_runs', 'ref')
    op.drop_column('sync_runs', 'source')
    op.drop_column('sync_runs', 'requested_at')
    op.alter_column('sync_runs', 'started_at', nullable=False)
    op.drop_column('sync_runs', 'trigger')
    op.execute("DROP TYPE sync_trigger_enum")
