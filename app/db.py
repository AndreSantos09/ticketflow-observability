"""Database access using a psycopg connection pool.

The pool is deliberately small (max_size=5) so the "leaky connections"
failure scenario exhausts it quickly and becomes observable.
"""
import logging

from psycopg_pool import ConnectionPool

from config import config

logger = logging.getLogger(__name__)

# Small pool on purpose: makes the leak scenario visible fast.
pool = ConnectionPool(
    conninfo=config.DATABASE_URL,
    min_size=1,
    max_size=5,
    timeout=5,  # seconds to wait for a free connection before raising
    open=False,
)


def open_pool() -> None:
    pool.open()
    logger.info("Database pool opened (max_size=%s)", pool.max_size)


def close_pool() -> None:
    pool.close()
    logger.info("Database pool closed")


def init_schema() -> None:
    """Create tables and seed a few events. Idempotent."""
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id          SERIAL PRIMARY KEY,
                    name        TEXT NOT NULL,
                    venue       TEXT NOT NULL,
                    total_seats INTEGER NOT NULL,
                    sold_seats  INTEGER NOT NULL DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS tickets (
                    id         SERIAL PRIMARY KEY,
                    event_id   INTEGER NOT NULL REFERENCES events(id),
                    buyer      TEXT NOT NULL,
                    quantity   INTEGER NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                );
                """
            )
            cur.execute("SELECT COUNT(*) FROM events;")
            (count,) = cur.fetchone()
            if count == 0:
                cur.execute(
                    """
                    INSERT INTO events (name, venue, total_seats) VALUES
                        ('Rock in Rio 2026', 'Parque Olimpico', 100000),
                        ('Show da Virada', 'Copacabana', 50000),
                        ('Festival de Jazz', 'Teatro Municipal', 1200);
                    """
                )
            conn.commit()
    logger.info("Schema initialised and seed data ready")
