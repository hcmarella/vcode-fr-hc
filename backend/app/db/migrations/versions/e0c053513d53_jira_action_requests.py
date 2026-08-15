"""jira action requests (human-approval gate for Jira writes)

Revision ID: e0c053513d53
Revises: e5a1f2ac0111
Create Date: 2026-08-15 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e0c053513d53'
down_revision: Union[str, None] = 'e5a1f2ac0111'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'jira_action_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'action_type',
            sa.Enum('create_issue', 'update_issue', name='jira_action_type_enum'),
            nullable=False,
        ),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('preview_text', sa.Text(), nullable=False),
        sa.Column(
            'status',
            sa.Enum(
                'pending', 'confirmed', 'rejected', 'executed', 'failed',
                name='jira_action_status_enum',
            ),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decided_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['requested_by_user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['decided_by_user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_jira_action_requests_status'), 'jira_action_requests', ['status']
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_jira_action_requests_status'), table_name='jira_action_requests')
    op.drop_table('jira_action_requests')
    op.execute("DROP TYPE jira_action_status_enum")
    op.execute("DROP TYPE jira_action_type_enum")
