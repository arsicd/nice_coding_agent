# from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from sqlalchemy import text

from alembic import context


from core.config import settings
from search.db.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
# if config.config_file_name is not None:
#     fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# Tables managed by PostgreSQL extensions (PostGIS, etc.) — never drop these.
EXTENSION_TABLES = {"spatial_ref_sys", "_typmod_cache"}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and name in EXTENSION_TABLES:
        return False
    return True


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return name == settings.db_schema
    return True


# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = settings.postgres_uri
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_object=include_object,
        include_name=include_name,
        include_schemas=False,
        version_table="alembic_version",
        version_table_schema=settings.db_schema,
    )

    with context.begin_transaction():
        context.execute(f'SET search_path TO "{settings.db_schema}", public')
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    configuration = context.config.get_section(context.config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.postgres_uri

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{settings.db_schema}"'))
        # 2. Pin search_path so unqualified table names resolve to our schema
        connection.execute(text(f'SET search_path TO "{settings.db_schema}", public'))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
            include_name=include_name,
            include_schemas=False,
            version_table="alembic_version",
            version_table_schema=settings.db_schema,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
