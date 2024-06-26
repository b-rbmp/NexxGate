"""Add index to granted

Revision ID: 1ea2205a4e05
Revises: a3fec4564817
Create Date: 2024-05-30 22:29:02.172221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1ea2205a4e05'
down_revision: Union[str, None] = 'a3fec4564817'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_AccessLog_granted'), 'AccessLog', ['granted'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_AccessLog_granted'), table_name='AccessLog')
    # ### end Alembic commands ###
