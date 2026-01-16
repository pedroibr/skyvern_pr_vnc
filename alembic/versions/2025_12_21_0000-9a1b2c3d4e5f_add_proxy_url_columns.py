"""add proxy_url columns

Revision ID: 9a1b2c3d4e5f
Revises: e393f33ec711
Create Date: 2025-12-21 00:00:00.000000+00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, None] = "e393f33ec711"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("proxy_url", sa.String(), nullable=True))
    op.add_column("workflow_runs", sa.Column("proxy_url", sa.String(), nullable=True))
    op.add_column("observer_cruises", sa.Column("proxy_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("observer_cruises", "proxy_url")
    op.drop_column("workflow_runs", "proxy_url")
    op.drop_column("tasks", "proxy_url")
