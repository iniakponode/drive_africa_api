from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import the Base and all your models
from safedrive.database.base import Base
from safedrive.models.trip import Trip
from safedrive.models.unsafe_behaviour import UnsafeBehaviour
from safedrive.models.location import Location
from safedrive.models.ai_model_input import AIModelInput
from safedrive.models.driving_tip import DrivingTip
from safedrive.models.driver_profile import DriverProfile
from safedrive.models.cause import Cause
from safedrive.models.embedding import Embedding
from safedrive.models.nlg_report import NLGReport
from safedrive.models.raw_sensor_data import RawSensorData

# Import other models as needed

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL here
# config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL', 'mysql+pymysql://dev2:ProgressIniks2018@localhost:3306/drive_safe_db'))

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
