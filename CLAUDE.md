# Deep Fractional

LangChain Deep Agents + CopilotKit for fractional executive job matching.

## Status: Phase 2.4 Complete

| Phase | Status |
|-------|--------|
| Phase 1: Core Setup | COMPLETE |
| Phase 2.1: Pydantic Schemas | COMPLETE |
| Phase 2.2: HITL Confirmation | COMPLETE |
| Phase 2.3: Neon Persistence | COMPLETE |
| Phase 2.4: Neon Auth | COMPLETE |
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

## Stack

| Component | Technology |
|-----------|------------|
| Agent Framework | LangChain Deep Agents (`create_deep_agent()`) |
| State Sync | CopilotKit AG-UI protocol |
| LLM | Gemini 2.0 Flash |
| Database | Neon PostgreSQL |
| Auth | Neon Auth (`@neondatabase/auth`) |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 15 + React 19 |
| Deploy | Railway (agent) + Vercel (frontend) |

## Key Files

**Agent:**
- `agent/agent.py` - Deep Agents graph with `interrupt_on` for HITL
- `agent/tools/onboarding.py` - 6 tools with Pydantic schemas + persistence
- `agent/persistence/neon.py` - asyncpg client for Neon PostgreSQL
- `agent/main.py` - FastAPI entrypoint

**Frontend:**
- `frontend/src/app/page.tsx` - CopilotKit UI + useHumanInTheLoop hooks
- `frontend/src/app/layout.tsx` - NeonAuthUIProvider + CopilotKit wrapper
- `frontend/src/lib/auth/client.ts` - Neon Auth client
- `frontend/src/app/auth/[path]/page.tsx` - Auth pages (sign-in, sign-up)
- `frontend/src/app/api/auth/[...path]/route.ts` - Auth API routes

## Environment Variables

**Railway (agent):**
- `GOOGLE_API_KEY` - Gemini API key
- `GOOGLE_MODEL` - gemini-2.0-flash
- `DATABASE_URL` - Neon PostgreSQL connection string

**Vercel (frontend):**
- `LANGGRAPH_DEPLOYMENT_URL` - Railway agent URL
- `NEON_AUTH_BASE_URL` - Neon Auth endpoint

## Database Schema

**Neon Project:** sweet-hat-02969611

**Tables:**
- `neon_auth.*` - Neon Auth tables (user, session, etc.)
- `public.user_profiles` - Onboarding data

```sql
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES neon_auth.user(id) ON DELETE CASCADE,
    role_preference VARCHAR(50),
    trinity VARCHAR(50),
    experience_years INTEGER,
    industries TEXT[],
    location VARCHAR(255),
    remote_preference VARCHAR(50),
    day_rate_min INTEGER,
    day_rate_max INTEGER,
    availability VARCHAR(100),
    onboarding_completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id)
);
```

## Key Patterns

1. **Agent Creation**: `create_deep_agent()` with `CopilotKitMiddleware()` + `interrupt_on`
2. **Tools**: `@tool(args_schema=PydanticModel)`, accept optional `user_id` for persistence
3. **HITL**: `useHumanInTheLoop` hooks render confirmation cards in chat
4. **Auth**: `NeonAuthUIProvider` wraps app, `authClient.useSession()` gets user
5. **State Sync**: `useCopilotReadable()` passes `user_id` + onboarding state to agent

## Auth Flow

1. User visits `/auth/sign-in` or `/auth/sign-up`
2. Neon Auth handles email OTP verification
3. Session stored, `UserButton` shows in header
4. `authClient.useSession()` provides `user.id`
5. `useCopilotReadable` passes `user_id` to agent
6. Tools persist to `user_profiles` table when `user_id` present

## Next Steps (Phase 2.5)

Add Job Search Agent:
1. Create `agent/tools/jobs.py` with search_jobs, match_jobs, save_job
2. Add job-search-agent to subagents in agent.py
3. Create jobs table in Neon
