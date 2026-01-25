# Deep Fractional

LangChain Deep Agents + CopilotKit for fractional executive job matching.

## Quick Start

```bash
# Agent (Python)
cd agent && uv run python main.py  # port 8123

# Frontend (Next.js)
cd frontend && npm run dev  # port 3000
```

## Documentation

- [Article Breakdown](docs/ARTICLE_BREAKDOWN.md) - Reference implementation patterns
- [Architecture](docs/ARCHITECTURE.md) - Multi-agent pattern
- [PRD](docs/PRD.md) - Product requirements
- [Checklist](docs/CHECKLIST.md) - Implementation progress

## Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain Deep Agents (`create_deep_agent()`) |
| State Sync | CopilotKit AG-UI protocol |
| LLM | Gemini 2.0 Flash (or OpenAI GPT-4) |
| Database | Neon PostgreSQL |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 15 + React 19 |
| Deploy | Railway (agent) + Vercel (frontend) |

## Key Patterns

1. **Agent Creation**: Use `create_deep_agent()` with `CopilotKitMiddleware()`
2. **Tools**: `@tool` decorator, return `Dict` for state updates
3. **Frontend Hook**: `useDefaultTool()` captures tool results
4. **State Readable**: `useCopilotReadable()` syncs frontend state to agent

## Environment Variables

**Agent (.env):**
```
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://...
```

**Frontend (.env.local):**
```
LANGGRAPH_DEPLOYMENT_URL=http://localhost:8123
```

## Project Structure

```
deep-fractional/
├── CLAUDE.md              # This file
├── docs/                  # Detailed documentation
├── agent/                 # Python backend
│   ├── main.py           # FastAPI entrypoint
│   ├── agent.py          # Deep Agents graph
│   ├── state.py          # State schemas
│   └── tools/            # Tool definitions
└── frontend/             # Next.js app
    └── src/
        ├── app/          # Routes + API
        └── components/   # UI components
```
