"""align_history_with_irrigation_result

Revision ID: 20260716_align_history_with_irrigation_result
Revises: 20260715_add_history_extended_fields
Create Date: 2026-07-16 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260716_align_history_with_irrigation_result'
down_revision = '20260715_add_history_extended_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Align irrigation history storage with the full IrrigationResult contract."""
    # Make this migration idempotent: only add columns that do not already exist.
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {c['name'] for c in insp.get_columns('irrigationhistory')}

    if 'success' not in existing_cols:
        op.add_column('irrigationhistory', sa.Column('success', sa.Boolean(), nullable=True))
    if 'was_manual_run' not in existing_cols:
        op.add_column('irrigationhistory', sa.Column('was_manual_run', sa.Boolean(), nullable=True))
    if 'carry_over_applied' not in existing_cols:
        op.add_column('irrigationhistory', sa.Column('carry_over_applied', sa.Boolean(), nullable=True))
    if 'dynamic_interval_enabled' not in existing_cols:
        op.add_column('irrigationhistory', sa.Column('dynamic_interval_enabled', sa.Boolean(), nullable=True))
    if 'irrigation_volume_threshold_percent' not in existing_cols:
        op.add_column('irrigationhistory', sa.Column('irrigation_volume_threshold_percent', sa.Integer(), nullable=True))

    # SQLite does not support ALTER COLUMN; use batch_alter_table which
    # rebuilds the table safely when needed. Only attempt if the column exists.
    if 'start_time' in existing_cols:
        with op.batch_alter_table('irrigationhistory') as batch_op:
            batch_op.alter_column('start_time', existing_type=sa.DateTime(), nullable=True)


def downgrade() -> None:
    """Revert the contract alignment columns."""
    # Only drop/revert columns if they exist (idempotent downgrade).
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_cols = {c['name'] for c in insp.get_columns('irrigationhistory')}

    if 'start_time' in existing_cols:
        with op.batch_alter_table('irrigationhistory') as batch_op:
            batch_op.alter_column('start_time', existing_type=sa.DateTime(), nullable=False)

    if 'irrigation_volume_threshold_percent' in existing_cols:
        op.drop_column('irrigationhistory', 'irrigation_volume_threshold_percent')
    if 'dynamic_interval_enabled' in existing_cols:
        op.drop_column('irrigationhistory', 'dynamic_interval_enabled')
    if 'carry_over_applied' in existing_cols:
        op.drop_column('irrigationhistory', 'carry_over_applied')
    if 'was_manual_run' in existing_cols:
        op.drop_column('irrigationhistory', 'was_manual_run')
    if 'success' in existing_cols:
        op.drop_column('irrigationhistory', 'success')
