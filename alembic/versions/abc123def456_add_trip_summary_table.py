"""add_trip_summary_table

Revision ID: abc123def456
Revises: <previous_revision>
Create Date: 2026-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'abc123def456'
down_revision = None  # Replace with actual previous revision
branch_labels = None
depends_on = None


def upgrade():
    # Create trip_summary table
    op.create_table(
        'trip_summary',
        sa.Column('trip_id', mysql.CHAR(36), nullable=False),
        sa.Column('total_distance', sa.Float, nullable=False, default=0.0),
        sa.Column('unsafe_count', sa.Integer, nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('trip_id'),
        sa.ForeignKeyConstraint(['trip_id'], ['trip.id'], ondelete='CASCADE'),
    )
    
    # Index for fast lookups
    op.create_index('idx_trip_summary_updated', 'trip_summary', ['last_updated'])
    
    # Populate with existing data
    op.execute("""
        INSERT INTO trip_summary (trip_id, total_distance, unsafe_count)
        SELECT 
            t.id,
            COALESCE(SUM(l.distance), 0) as total_distance,
            (SELECT COUNT(*) FROM unsafe_behaviour ub WHERE ub.trip_id = t.id) as unsafe_count
        FROM trip t
        LEFT JOIN raw_sensor_data r ON r.trip_id = t.id
        LEFT JOIN location l ON l.id = r.location_id
        GROUP BY t.id
    """)


def downgrade():
    op.drop_table('trip_summary')
