# Deep Fractional

LangChain Deep Agents + CopilotKit for fractional executive job matching.

## Status: Phase 2 In Progress

| Phase | Status |
|-------|--------|
| Phase 1: Core Setup | COMPLETE |
| Phase 2.1: Pydantic Schemas | COMPLETE |
| Phase 2.2: HITL Confirmation | IN PROGRESS |
| Phase 2.3: Neon Persistence | Pending |
| Phase 2.4: Neon Auth | Pending |
| Phase 2.5: Job Search Agent | Pending |
| Phase 2.6: Coaching Agent | Pending |

## Production URLs

| Service | URL |
|---------|-----|
| Frontend (Vercel) | https://deep-fractional-web.vercel.app |
| Agent (Railway) | https://agent-production-ccb0.up.railway.app |
| GitHub | https://github.com/Londondannyboy/deep-fractional |

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
| LLM | Gemini 2.0 Flash |
| Database | Neon PostgreSQL |
| Auth | Neon Auth (Better Auth) |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 15 + React 19 |
| Deploy | Railway (agent) + Vercel (frontend) |

## Key Patterns

1. **Agent Creation**: Use `create_deep_agent()` with `CopilotKitMiddleware()`
2. **Tools**: `@tool` decorator with `args_schema` (Pydantic), return `Dict` for state updates
3. **Frontend Hook**: `useDefaultTool()` captures tool results
4. **State Readable**: `useCopilotReadable()` syncs frontend state to agent

## Environment Variables

**Agent (.env):**
```
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://neondb_owner:...@ep-divine-waterfall-abig6fic-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require
```

**Frontend (.env.local):**
```
LANGGRAPH_DEPLOYMENT_URL=https://agent-production-ccb0.up.railway.app
```

## Neon Database

**Connection String:**
```
postgresql://neondb_owner:npg_h4SxyI8GrpzN@ep-divine-waterfall-abig6fic-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require
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
│   └── tools/            # Tool definitions (Pydantic schemas)
└── frontend/             # Next.js app
    └── src/
        ├── app/          # Routes + API
        └── components/   # UI components
```

## HITL Implementation (Phase 2.2)

Human-in-the-loop confirmation added:

**Backend (`agent/agent.py`):**
```python
interrupt_on = {
    "confirm_role_preference": True,
    "confirm_trinity": True,
    "confirm_experience": True,
    "confirm_location": True,
    "confirm_search_prefs": True,
    "complete_onboarding": True,
}

agent_graph = create_deep_agent(
    ...
    interrupt_on=interrupt_on,  # HITL: pause for user confirmation
)
```

**Frontend (`frontend/src/app/page.tsx`):**
- Uses `useHumanInTheLoop` hook from `@copilotkit/react-core`
- Each onboarding tool has a colored confirmation card
- User clicks "Confirm" to proceed or "Cancel" to reject

## Next Steps (Phase 2.3)

Add Neon persistence:
1. Create `agent/persistence/neon.py` with asyncpg
2. Create database schema for user profiles
3. Update tools to persist data to Neon
