"""
PostgreSQL checkpointer for LangGraph conversation persistence.

Uses AsyncPostgresSaver from langgraph-checkpoint-postgres to persist
conversation state across server restarts.
"""

import os
import asyncio
from typing import Optional

import asyncpg
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


_pool: Optional[asyncpg.Pool] = None
_checkpointer: Optional[AsyncPostgresSaver] = None
_setup_done: bool = False


async def create_pool() -> asyncpg.Pool:
    """Create and return an asyncpg connection pool."""
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set for checkpointer")

    pool = await asyncpg.create_pool(database_url)
    print("[CHECKPOINTER] Created asyncpg connection pool")
    return pool


async def init_checkpointer() -> AsyncPostgresSaver:
    """
    Initialize checkpointer at startup.

    Call this in FastAPI lifespan to ensure tables are ready.
    Returns the checkpointer instance for use with create_deep_agent.
    """
    global _pool, _checkpointer, _setup_done

    if _pool is None:
        _pool = await create_pool()

    if _checkpointer is None:
        _checkpointer = AsyncPostgresSaver(_pool)
        print("[CHECKPOINTER] Created AsyncPostgresSaver")

    # Setup tables on first use
    if not _setup_done:
        try:
            await _checkpointer.setup()
            _setup_done = True
            print("[CHECKPOINTER] Database tables initialized")
        except Exception as e:
            # Tables may already exist, which is fine
            if "already exists" in str(e).lower():
                _setup_done = True
                print("[CHECKPOINTER] Tables already exist, skipping setup")
            else:
                print(f"[CHECKPOINTER] Setup warning: {e}")
                _setup_done = True  # Continue anyway, tables might exist

    return _checkpointer


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get the PostgreSQL checkpointer (after init).

    Returns the cached instance created during init.
    """
    global _checkpointer

    if _checkpointer is None:
        return await init_checkpointer()

    return _checkpointer


async def close_checkpointer():
    """Close the checkpointer connection pool."""
    global _pool, _checkpointer, _setup_done

    if _pool is not None:
        try:
            await _pool.close()
            print("[CHECKPOINTER] Connection pool closed")
        except Exception as e:
            print(f"[CHECKPOINTER] Close warning: {e}")
        finally:
            _pool = None
            _checkpointer = None
            _setup_done = False


def get_sync_checkpointer() -> Optional[AsyncPostgresSaver]:
    """
    Get checkpointer synchronously for agent build.

    Returns None if not initialized yet. The agent will be
    reconfigured with the real checkpointer after init.

    NOTE: For proper persistence, call init_checkpointer() in
    FastAPI lifespan before handling requests.
    """
    return _checkpointer


def get_cached_checkpointer() -> Optional[AsyncPostgresSaver]:
    """
    Get the cached checkpointer instance without creating one.

    Returns the instance if already initialized, None otherwise.
    Used by main.py to pass to the agent after async initialization.
    """
    return _checkpointer
