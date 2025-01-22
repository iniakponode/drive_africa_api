"""Corrected wrong Base imports in alcoholquestionnaire Model

Revision ID: b3076df7bfa5
Revises: 54ff87bff66e
Create Date: 2025-01-16 15:35:44.608585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types.uuid import UUIDType


# revision identifiers, used by Alembic.
revision: str = 'b3076df7bfa5'
down_revision: Union[str, None] = '54ff87bff66e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('alcohol_questionnaire',
    sa.Column('id', UUIDType(), nullable=False),
    sa.Column('driverProfileId', UUIDType(), nullable=False),
    sa.Column('drankAlcohol', sa.Boolean(), nullable=False),
    sa.Column('selectedAlcoholTypes', sa.Text(), nullable=False),
    sa.Column('beerQuantity', sa.String(length=255), nullable=False),
    sa.Column('wineQuantity', sa.String(length=255), nullable=False),
    sa.Column('spiritsQuantity', sa.String(length=255), nullable=False),
    sa.Column('firstDrinkTime', sa.String(length=255), nullable=False),
    sa.Column('lastDrinkTime', sa.String(length=255), nullable=False),
    sa.Column('emptyStomach', sa.Boolean(), nullable=False),
    sa.Column('caffeinatedDrink', sa.Boolean(), nullable=False),
    sa.Column('impairmentLevel', sa.Integer(), nullable=False),
    sa.Column('plansToDrive', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['driverProfileId'], ['driver_profile.driverProfileId'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('alcohol_questionnaire')
    # ### end Alembic commands ###