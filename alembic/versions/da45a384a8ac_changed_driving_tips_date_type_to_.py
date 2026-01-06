"""Changed Driving Tips date type to DateTime

Revision ID: da45a384a8ac
Revises: 3f37686ddcb9
Create Date: 2025-02-04 07:35:44.173897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da45a384a8ac'
down_revision: Union[str, None] = '3f37686ddcb9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        inspector = sa.inspect(bind)
        raw_fk_name = None
        raw_has_trip_fk = False
        for fk in inspector.get_foreign_keys("raw_sensor_data"):
            if fk.get("referred_table") == "trip" and fk.get("constrained_columns") == ["trip_id"]:
                raw_has_trip_fk = True
                raw_fk_name = fk.get("name")
                break
        trip_fk_name = None
        trip_has_profile_fk = False
        for fk in inspector.get_foreign_keys("trip"):
            if fk.get("referred_table") == "driver_profile" and fk.get("constrained_columns") == ["driverProfileId"]:
                trip_has_profile_fk = True
                trip_fk_name = fk.get("name")
                break

        with op.batch_alter_table("raw_sensor_data") as batch_op:
            if raw_fk_name:
                try:
                    batch_op.drop_constraint(raw_fk_name, type_='foreignkey')
                except ValueError:
                    pass
            if raw_fk_name or not raw_has_trip_fk:
                batch_op.create_foreign_key(
                    None,
                    "trip",
                    ["trip_id"],
                    ["id"],
                    ondelete="CASCADE",
                )
        with op.batch_alter_table("trip") as batch_op:
            if trip_fk_name:
                try:
                    batch_op.drop_constraint(trip_fk_name, type_='foreignkey')
                except ValueError:
                    pass
            if trip_fk_name or not trip_has_profile_fk:
                batch_op.create_foreign_key(
                    None,
                    "driver_profile",
                    ["driverProfileId"],
                    ["driverProfileId"],
                    ondelete="CASCADE",
                )
    else:
        op.drop_constraint('raw_sensor_data_ibfk_2', 'raw_sensor_data', type_='foreignkey')
        op.create_foreign_key(None, 'raw_sensor_data', 'trip', ['trip_id'], ['id'], ondelete='CASCADE')
        op.drop_constraint('trip_ibfk_1', 'trip', type_='foreignkey')
        op.create_foreign_key(None, 'trip', 'driver_profile', ['driverProfileId'], ['driverProfileId'], ondelete='CASCADE')


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        inspector = sa.inspect(bind)
        trip_fk_name = None
        for fk in inspector.get_foreign_keys("trip"):
            if fk.get("referred_table") == "driver_profile" and fk.get("constrained_columns") == ["driverProfileId"]:
                trip_fk_name = fk.get("name")
                break
        raw_fk_name = None
        for fk in inspector.get_foreign_keys("raw_sensor_data"):
            if fk.get("referred_table") == "trip" and fk.get("constrained_columns") == ["trip_id"]:
                raw_fk_name = fk.get("name")
                break

        with op.batch_alter_table("trip") as batch_op:
            if trip_fk_name:
                try:
                    batch_op.drop_constraint(trip_fk_name, type_='foreignkey')
                except ValueError:
                    pass
            batch_op.create_foreign_key(
                'trip_ibfk_1',
                "driver_profile",
                ["driverProfileId"],
                ["driverProfileId"],
            )
        with op.batch_alter_table("raw_sensor_data") as batch_op:
            if raw_fk_name:
                try:
                    batch_op.drop_constraint(raw_fk_name, type_='foreignkey')
                except ValueError:
                    pass
            batch_op.create_foreign_key(
                'raw_sensor_data_ibfk_2',
                "trip",
                ["trip_id"],
                ["id"],
            )
    else:
        op.drop_constraint(None, 'trip', type_='foreignkey')
        op.create_foreign_key('trip_ibfk_1', 'trip', 'driver_profile', ['driverProfileId'], ['driverProfileId'])
        op.drop_constraint(None, 'raw_sensor_data', type_='foreignkey')
        op.create_foreign_key('raw_sensor_data_ibfk_2', 'raw_sensor_data', 'trip', ['trip_id'], ['id'])
