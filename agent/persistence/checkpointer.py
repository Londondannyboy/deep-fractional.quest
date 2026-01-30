"""
PostgreSQL checkpointer for LangGraph conversation persistence.

Uses AsyncPostgresSaver from langgraph-checkpoint-postgres to persist
conversation state across server restarts.
"""

import os
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


_checkpointer: Optional[AsyncPostgresSaver] = None
_setup_done: bool = False


async def get_checkpointer() -> AsyncPostgresSaver:
    """
    Get or create the PostgreSQL checkpointer.

    Uses DATABASE_URL environment variable for connection.
    Runs setup() on first call to create required tables.
    """
    global _checkpointer, _setup_done

    if _checkpointer is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not set for checkpointer")

        # Create checkpointer from connection string
        _checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
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


async def init_checkpointer() -> AsyncPostgresSaver:
    """
    Initialize checkpointer at startup.

    Call this in FastAPI lifespan to ensure tables are ready.
    Returns the checkpointer instance for use with create_deep_agent.
    """
    return await get_checkpointer()


async def close_checkpointer():
    """Close the checkpointer connection pool."""
    global _checkpointer, _setup_done

    if _checkpointer is not None:
        # AsyncPostgresSaver from_conn_string creates a pool internally
        # It should be closed when done
        try:
            await _checkpointer.conn.close()
            print("[CHECKPOINTER] Connection closed")
        except Exception as e:
            print(f"[CHECKPOINTER] Close warning: {e}")
        finally:
            _checkpointer = None
            _setup_done = False


# For sync context (agent build)
def get_sync_checkpointer() -> AsyncPostgresSaver:
    """
    Get checkpointer synchronously for agent build.

    NOTE: Caller must ensure setup() is called before graph execution.
    Use init_checkpointer() in FastAPI lifespan for proper async setup.
    """
    global _checkpointer

    if _checkpointer is None:
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not set for checkpointer")

        _checkpointer = AsyncPostgresSaver.from_conn_string(database_url)
        print("[CHECKPOINTER] Created AsyncPostgresSaver (sync context)")

    return _checkpointer
