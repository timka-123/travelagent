"""improve travel note

Revision ID: fa9ca9e0e5e7
Revises: ed925f3428d4
Create Date: 2024-03-25 19:28:39.194828

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa9ca9e0e5e7'
down_revision: Union[str, None] = 'ed925f3428d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('travel_notes', sa.Column('name', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('travel_notes', 'name')
    # ### end Alembic commands ###