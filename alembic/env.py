from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os

# this is the Alembic Config object, which provides access to the values
# within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

import logging

# Make sure the project root is on sys.path so `import app` works when
# alembic is invoked directly (without using `scripts/migrate.sh`).
import sys
here = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(here, ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the application's SQLAlchemy engine and models metadata.
# We attempt to import the app's engine, but regardless try to import
# all model modules so `SQLModel.metadata` is populated. Any import
# errors are logged to aid debugging.
env_logger = logging.getLogger("alembic.env")

engine = None
target_metadata = None

try:
    from app.services import database as _database
    engine = getattr(_database, "engine", None)
except Exception:
    env_logger.exception("Failed to import app.services.database; continuing without engine")

try:
    from sqlmodel import SQLModel
    target_metadata = SQLModel.metadata
except Exception:
    env_logger.exception("Failed to import SQLModel; target_metadata will be None")

# If engine couldn't be imported from the app, try to construct one from
# environment variables so we can still run online migrations when alembic
# is invoked directly.
if engine is None:
    try:
        from sqlalchemy import create_engine

        db_user = os.environ.get("DB_USER") or os.environ.get("POSTGRES_USER")
        db_pass = os.environ.get("DB_PASSWORD") or os.environ.get("POSTGRES_PASSWORD")
        db_host = os.environ.get("DB_HOST_IP") or os.environ.get("DB_HOST") or os.environ.get("DB_HOSTNAME") or "db"
        db_name = os.environ.get("DB_NAME") or os.environ.get("POSTGRES_DB")

        if db_user and db_pass and db_host and db_name:
            url = f"postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:5432/{db_name}"
            env_logger.info("Constructed DB URL from env for alembic: %s", url)
            engine = create_engine(url, pool_pre_ping=True)
        else:
            env_logger.info("Insufficient env vars to construct DB URL; engine remains None")
    except Exception:
        env_logger.exception("Failed to construct engine from environment variables")

# Import all model modules under app.models so classes register in metadata.
try:
    import importlib
    import pkgutil

    import app.models as models_pkg
    pkg_path = getattr(models_pkg, "__path__", None)
    if pkg_path is not None:
        for finder, name, ispkg in pkgutil.iter_modules(pkg_path):
            try:
                importlib.import_module(f"app.models.{name}")
            except Exception:
                env_logger.exception(f"Failed to import app.models.{name}")
except Exception:
    env_logger.exception("Failed to import app.models package")

# Log what tables are present in metadata for visibility
try:
    if target_metadata is not None:
        env_logger.info("Tables in SQLModel.metadata: %s", list(target_metadata.tables.keys()))
    else:
        env_logger.info("No target_metadata available (SQLModel import failed)")
except Exception:
    env_logger.exception("Error while inspecting target_metadata")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine if engine is not None else engine_from_config(
        config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
