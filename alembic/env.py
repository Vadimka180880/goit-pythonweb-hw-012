import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

load_dotenv()

pythonpath = os.getenv("PYTHONPATH")
if pythonpath and pythonpath not in sys.path:
    sys.path.insert(0, pythonpath)
    print(f"Added PYTHONPATH from .env: {pythonpath}")

project_root = Path(__file__).resolve().parents[1]
print(f"Project root: {project_root}")
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
    print(f"Added to sys.path: {sys.path}")

try:
    from app.src.database.base import engine, Base
    from app.src.config.config import settings
    print("Successfully imported engine, Base, and settings")
except ImportError as e:
    print(f"Import error: {e}")
    print("Current sys.path:", sys.path)
    raise

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = str(settings.sync_database_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = str(settings.sync_database_url)
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()