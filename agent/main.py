"""
FastAPI entrypoint for Fractional Quest agent.

Exposes AG-UI endpoint for CopilotKit integration.
"""

import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent

from persistence.checkpointer import init_checkpointer, close_checkpointer, get_cached_checkpointer


# =============================================================================
# Synchronous Initialization
# =============================================================================

# Initialize checkpointer BEFORE building agent (critical for persistence)
# Handle both cases: running under uvicorn (has loop) or directly (no loop)
print("[INIT] Initializing checkpointer synchronously...")


def _init_checkpointer_sync():
    """Initialize checkpointer, handling event loop edge cases."""
    try:
        # Try to get existing loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Loop is running (uvicorn) - use nest_asyncio pattern
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, init_checkpointer())
                future.result(timeout=30)
            print("[INIT] Checkpointer ready (thread pool)")
        else:
            # Loop exists but not running - use run_until_complete
            loop.run_until_complete(init_checkpointer())
            print("[INIT] Checkpointer ready (existing loop)")
    except RuntimeError:
        # No event loop at all - create one
        asyncio.run(init_checkpointer())
        print("[INIT] Checkpointer ready (new loop)")


try:
    _init_checkpointer_sync()
except Exception as e:
    print(f"[INIT] Checkpointer warning: {e}")

# NOW import and build agent (checkpointer is available)
from agent import build_agent


# =============================================================================
# FastAPI Lifespan
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle.

    Checkpointer is already initialized at module load.
    Lifespan handles cleanup on shutdown.
    """
    print("[LIFESPAN] Starting up...")
    print(f"[LIFESPAN] Checkpointer available: {get_cached_checkpointer() is not None}")

    yield

    # Cleanup on shutdown
    print("[LIFESPAN] Shutting down...")
    await close_checkpointer()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Fractional Quest Agent",
    description="Deep Agents backend for fractional executive career assistance",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Build and Register Agent
# =============================================================================

try:
    agent_graph = build_agent()

    add_langgraph_fastapi_endpoint(
        app=app,
        agent=LangGraphAGUIAgent(
            name="fractional_quest",
            description="AI career assistant for fractional executives",
            graph=agent_graph,
        ),
        path="/",
    )

    print("[MAIN] Agent registered at /")

except Exception as e:
    print(f"[ERROR] Failed to build agent: {e}")
    raise


# =============================================================================
# Health & Debug Endpoints
# =============================================================================

@app.get("/healthz")
async def health_check():
    """Health check for orchestration."""
    return {
        "status": "healthy",
        "service": "fractional-quest-agent",
        "version": "1.0.0",
    }


@app.get("/debug")
async def debug_info():
    """Debug information."""
    return {
        "agent_name": "fractional_quest",
        "google_model": os.environ.get("GOOGLE_MODEL", "gemini-2.0-flash"),
        "has_api_key": bool(os.environ.get("GOOGLE_API_KEY")),
    }


# =============================================================================
# Run Server
# =============================================================================

def main():
    """Run the uvicorn server."""
    host = os.getenv("SERVER_HOST", "0.0.0.0")
    # Railway uses PORT, locally we use SERVER_PORT
    port = int(os.getenv("PORT", os.getenv("SERVER_PORT", "8123")))

    print(f"[MAIN] Starting server on {host}:{port}")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level="info",
    )


if __name__ == "__main__":
    main()
