import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import MetaData, create_engine, text
from sqlalchemy.sql.compiler import IdentifierPreparer
from sqlalchemy.orm import declarative_base, sessionmaker


backend_env = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(backend_env)
load_dotenv()


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "postgresql://postgres:Rohit17240@localhost:5432/taskManager")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


SQLALCHEMY_DATABASE_URL = _database_url()
connect_args = {"check_same_thread": False} if SQLALCHEMY_DATABASE_URL.startswith("sqlite") else {}
DB_SCHEMA = os.getenv("DB_SCHEMA", "team_task_manager_app") if not SQLALCHEMY_DATABASE_URL.startswith("sqlite") else None

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base(metadata=MetaData(schema=DB_SCHEMA))


def init_db() -> None:
    with engine.begin() as conn:
        if DB_SCHEMA:
            preparer = IdentifierPreparer(conn.dialect)
            quoted_schema = preparer.quote_schema(DB_SCHEMA)
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {quoted_schema}"))
        Base.metadata.create_all(bind=conn)
        if DB_SCHEMA and engine.dialect.name == "postgresql":
            run_postgres_migrations(conn, DB_SCHEMA)


def run_postgres_migrations(conn, schema: str) -> None:
    preparer = IdentifierPreparer(conn.dialect)
    quoted_schema = preparer.quote_schema(schema)
    schema_literal = schema.replace("'", "''")
    conn.execute(
        text(
            f"""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_type t
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = 'projectrole'
                    AND n.nspname = '{schema_literal}'
                ) THEN
                    CREATE TYPE {quoted_schema}.projectrole AS ENUM ('admin', 'member');
                END IF;
            END $$;
            """
        )
    )
    conn.execute(
        text(
            f"""
            ALTER TABLE {quoted_schema}.memberships
            ADD COLUMN IF NOT EXISTS role {quoted_schema}.projectrole NOT NULL DEFAULT 'member'
            """
        )
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
