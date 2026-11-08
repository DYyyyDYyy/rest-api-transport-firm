"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-11-08 17:46:21.603429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('clients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('address', sa.String(length=255), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('drivers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(length=150), nullable=False),
    sa.Column('phone', sa.String(length=20), nullable=False),
    sa.Column('license_number', sa.String(length=30), nullable=False),
    sa.Column('license_categories', sa.String(length=20), nullable=False),
    sa.Column('experience_years', sa.Integer(), nullable=False),
    sa.CheckConstraint('experience_years >= 0', name='ck_drivers_experience'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('license_number'),
    sa.UniqueConstraint('phone')
    )
    op.create_table('vehicles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('plate_number', sa.String(length=15), nullable=False),
    sa.Column('make', sa.String(length=50), nullable=False),
    sa.Column('model', sa.String(length=50), nullable=False),
    sa.Column('capacity_kg', sa.Integer(), nullable=False),
    sa.Column('is_available', sa.Boolean(), server_default='true', nullable=False),
    sa.Column('unavailable_reason', sa.String(length=255), nullable=True),
    sa.CheckConstraint('capacity_kg > 0', name='ck_vehicles_capacity'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('plate_number')
    )
    op.create_table('orders',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('client_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('new', 'planned', 'in_progress', 'completed', 'cancelled', name='orderstatus', native_enum=False, length=20), nullable=False),
    sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('price >= 0', name='ck_orders_price'),
    sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('trip_details',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('vehicle_id', sa.Integer(), nullable=True),
    sa.Column('origin', sa.String(length=255), nullable=False),
    sa.Column('destination', sa.String(length=255), nullable=False),
    sa.Column('distance_km', sa.Integer(), nullable=False),
    sa.Column('cargo_weight_kg', sa.Integer(), nullable=False),
    sa.Column('planned_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('planned_end', sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint('cargo_weight_kg > 0', name='ck_trip_details_weight'),
    sa.CheckConstraint('distance_km > 0', name='ck_trip_details_distance'),
    sa.CheckConstraint('planned_end > planned_start', name='ck_trip_details_period'),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('order_id')
    )
    op.create_table('trip_drivers',
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('driver_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['trip_id'], ['trip_details.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('trip_id', 'driver_id')
    )
    op.create_table('trip_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('trip_id', sa.Integer(), nullable=False),
    sa.Column('driver_id', sa.Integer(), nullable=False),
    sa.Column('actual_start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('actual_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('driver_comment', sa.Text(), nullable=True),
    sa.CheckConstraint('actual_end IS NULL OR actual_end >= actual_start', name='ck_trip_logs_period'),
    sa.ForeignKeyConstraint(['driver_id'], ['drivers.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['trip_id'], ['trip_details.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('trip_logs')
    op.drop_table('trip_drivers')
    op.drop_table('trip_details')
    op.drop_table('orders')
    op.drop_table('vehicles')
    op.drop_table('drivers')
    op.drop_table('clients')
