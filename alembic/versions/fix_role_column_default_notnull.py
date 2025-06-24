"""fix role column: set default, not null, and update nulls

Revision ID: fix_role_column_default_notnull
Revises: fff54388e2c7
Create Date: 2025-06-23 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'fix_role_column_default_notnull'
down_revision = 'fff54388e2c7'
branch_labels = None
depends_on = None

def upgrade():
    # Set all NULL roles to 'user'
    op.execute("UPDATE users SET role='user' WHERE role IS NULL")
    # Alter column: set default and not null
    op.alter_column('users', 'role',
        existing_type=sa.String(),
        nullable=False,
        server_default='user',
    )

def downgrade():
    op.alter_column('users', 'role',
        existing_type=sa.String(),
        nullable=True,
        server_default=None,
    )
