"""
PostgreSQL checkpointer for LangGraph conversation persistence.

Uses AsyncPostgresSaver from langgraph-checkpoint-postgres to persist
conversation state across server restarts.

NOTE: langgraph-checkpoint-postgres 3.x's from_conn_string returns a
context manager. We manually enter it to get a persistent instance.
"""

import os
from typing import Optional, Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


_checkpointer: Optional[AsyncPostgresSaver] = None
_context_manager: Optional[Any] = None
_setup_done: bool = False


async def init_checkpointer() -> AsyncPostgresSaver:
    """
    Initialize checkpointer at startup.

    Call this in FastAPI lifespan to ensure tables are ready.
    Returns the checkpointer instance for use with create_deep_agent.
    """
    global _checkpointer, _context_manager, _setup_done

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL not set for checkpointer")

    if _checkpointer is None:
        # langgraph-checkpoint-postgres 3.x: from_conn_string returns async context manager
        # We manually enter it to get a persistent checkpointer instance
        _context_manager = AsyncPostgresSaver.from_conn_string(database_url)
        _checkpointer = await _context_manager.__aenter__()
        print("[CHECKPOINTER] Created AsyncPostgresSaver (entered context)")

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
    """Close the checkpointer connection."""
    global _checkpointer, _context_manager, _setup_done

    if _context_manager is not None:
        try:
            # Properly exit the async context manager
            await _context_manager.__aexit__(None, None, None)
            print("[CHECKPOINTER] Closed checkpointer context")
        except Exception as e:
            print(f"[CHECKPOINTER] Close warning: {e}")
        finally:
            _checkpointer = None
            _context_manager = None
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
