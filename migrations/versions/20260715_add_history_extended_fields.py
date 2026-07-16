"""add_history_extended_fields

Revision ID: 20260715_add_history_extended_fields
Revises: 47c4a84f414e
Create Date: 2026-07-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260715_add_history_extended_fields'
down_revision = '47c4a84f414e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add extended irrigation history fields (nullable for backward compatibility)."""
    op.add_column('irrigationhistory', sa.Column('base_water_amount', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('standard_conditions_solar', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('standard_conditions_rain', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('standard_conditions_temp', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('actual_solar', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('actual_rain', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('actual_temp', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('carry_over', sa.Boolean(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('even_area_mode', sa.Boolean(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('target_mm', sa.Float(), nullable=True))
    op.add_column('irrigationhistory', sa.Column('actual_mm', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove extended irrigation history fields."""
    op.drop_column('irrigationhistory', 'actual_mm')
    op.drop_column('irrigationhistory', 'target_mm')
    op.drop_column('irrigationhistory', 'even_area_mode')
    op.drop_column('irrigationhistory', 'carry_over')
    op.drop_column('irrigationhistory', 'actual_temp')
    op.drop_column('irrigationhistory', 'actual_rain')
    op.drop_column('irrigationhistory', 'actual_solar')
    op.drop_column('irrigationhistory', 'standard_conditions_temp')
    op.drop_column('irrigationhistory', 'standard_conditions_rain')
    op.drop_column('irrigationhistory', 'standard_conditions_solar')
    op.drop_column('irrigationhistory', 'base_water_amount')
