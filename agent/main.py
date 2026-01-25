"""
FastAPI entrypoint for Fractional Quest agent.

Exposes AG-UI endpoint for CopilotKit integration.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from copilotkit import LangGraphAGUIAgent

from agent import build_agent


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Fractional Quest Agent",
    description="Deep Agents backend for fractional executive career assistance",
    version="1.0.0",
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
    port = int(os.getenv("SERVER_PORT", "8123"))

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
