"""expand role_enum: member/admin -> developer/business/manager/admin

Revision ID: cbbbbff1cd88
Revises: e0c053513d53
Create Date: 2026-08-15 22:10:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'cbbbbff1cd88'
down_revision: Union[str, None] = 'e0c053513d53'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Full type swap rather than ALTER TYPE ... ADD VALUE -- unlike the
# sync_run_status_enum migration, this one also needs to remove a value
# ('member', replaced by 'developer'/'business'/'manager'), which Postgres
# can't do via ADD VALUE at all. A fresh type + USING cast handles add and
# remove in one step, and -- because it's a new type rather than adding a
# value to the existing one -- can run in a single transaction with no
# same-transaction-usage restriction.


def upgrade() -> None:
    op.execute("CREATE TYPE role_enum_new AS ENUM ('developer', 'business', 'manager', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users ALTER COLUMN role TYPE role_enum_new
        USING (CASE role::text WHEN 'member' THEN 'developer' ELSE role::text END)::role_enum_new
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'developer'")
    op.execute("DROP TYPE role_enum")
    op.execute("ALTER TYPE role_enum_new RENAME TO role_enum")


def downgrade() -> None:
    op.execute("CREATE TYPE role_enum_old AS ENUM ('member', 'admin')")
    op.execute("ALTER TABLE users ALTER COLUMN role DROP DEFAULT")
    op.execute(
        """
        ALTER TABLE users ALTER COLUMN role TYPE role_enum_old
        USING (CASE role::text WHEN 'admin' THEN 'admin' ELSE 'member' END)::role_enum_old
        """
    )
    op.execute("ALTER TABLE users ALTER COLUMN role SET DEFAULT 'member'")
    op.execute("DROP TYPE role_enum")
    op.execute("ALTER TYPE role_enum_old RENAME TO role_enum")
