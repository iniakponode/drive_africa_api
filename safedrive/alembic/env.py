from logging.config import fileConfig
import os
from sqlalchemy import create_engine, pool
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

# Alembic Config object for access to .ini file values
config = context.config

# Set database URL from environment
database_url = os.getenv('DATABASE_URL')
if not database_url:
    raise RuntimeError("DATABASE_URL environment variable is not set.")
config.set_main_option('sqlalchemy.url', database_url)

# Interpret config file for logging
fileConfig(config.config_file_name)

# MetaData for 'autogenerate' support
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
    connectable = create_engine(database_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()