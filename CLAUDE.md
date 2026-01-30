# Deep Fractional

LangChain Deep Agents + CopilotKit for fractional executive job matching.

## Status: Phase 3 Complete - Ready for Phase 4

| Phase | Status |
|-------|--------|
| Phase 1: Core Setup | COMPLETE |
| Phase 2.1: Pydantic Schemas | COMPLETE |
| Phase 2.2: HITL Confirmation | COMPLETE |
| Phase 2.3: Neon Persistence | COMPLETE |
| Phase 2.4: Neon Auth | COMPLETE |
| Phase 2.5: Job Search Agent | COMPLETE |
| Phase 2.6: Coaching Agent | COMPLETE (code) |
| Phase 2.7: PostgreSQL Checkpointer | COMPLETE |
| Phase 3: Hume EVI Voice | COMPLETE |
| Phase 4: Production Hardening | IN PROGRESS |

**Note:** Coaching tables need manual migration - see RESTART_PROMPT.md

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
| Checkpointer | AsyncPostgresSaver (langgraph-checkpoint-postgres) |
| Memory | Zep Cloud (cross-session facts/preferences) |
| Voice | Hume EVI (@humeai/voice-react) |
| Backend | FastAPI + uvicorn |
| Frontend | Next.js 15 + React 19 |
| Deploy | Railway (agent) + Vercel (frontend) |

## Key Files

**Agent:**
- `agent/agent.py` - Deep Agents graph with 3 subagents + HITL
- `agent/tools/onboarding.py` - 6 onboarding tools
- `agent/tools/jobs.py` - 6 job search tools
- `agent/tools/coaching.py` - 5 coaching tools
- `agent/tools/memory.py` - Zep memory integration
- `agent/persistence/neon.py` - asyncpg client for Neon PostgreSQL
- `agent/persistence/checkpointer.py` - PostgreSQL checkpointer for conversation persistence
- `agent/migrations/002_create_jobs_tables.sql` - Jobs schema
- `agent/migrations/003_create_coaching_tables.sql` - Coaching schema
- `agent/main.py` - FastAPI entrypoint with lifespan

**Frontend:**
- `frontend/src/app/page.tsx` - CopilotKit UI + useHumanInTheLoop hooks + VoiceInput
- `frontend/src/app/layout.tsx` - NeonAuthUIProvider + CopilotKit wrapper
- `frontend/src/components/VoiceInput.tsx` - Hume EVI voice component
- `frontend/src/app/api/hume-token/route.ts` - Hume OAuth2 token generation
- `frontend/src/lib/auth/client.ts` - Neon Auth client
- `frontend/src/app/auth/[path]/page.tsx` - Auth pages (sign-in, sign-up)
- `frontend/src/app/api/auth/[...path]/route.ts` - Auth API routes

## Environment Variables

**Railway (agent):**
- `GOOGLE_API_KEY` - Gemini API key
- `GOOGLE_MODEL` - gemini-2.0-flash
- `DATABASE_URL` - Neon PostgreSQL connection string
- `ZEP_API_KEY` - Zep Cloud API key (optional)

**Vercel (frontend):**
- `LANGGRAPH_DEPLOYMENT_URL` - Railway agent URL
- `NEON_AUTH_BASE_URL` - Neon Auth endpoint
- `HUME_API_KEY` - Hume API key (server-side)
- `HUME_SECRET_KEY` - Hume secret key (server-side)
- `NEXT_PUBLIC_HUME_CONFIG_ID` - Hume EVI config ID (optional)

## Database Schema

**Neon Project:** sweet-hat-02969611

**Tables:**
- `neon_auth.*` - Neon Auth tables (user, session, etc.)
- `public.user_profiles` - Onboarding data
- `public.jobs` - Job listings
- `public.saved_jobs` - User saved jobs with status tracking
- `public.coaches` - Executive coach profiles
- `public.coaching_sessions` - User coaching session bookings
- `checkpoint_*` - LangGraph checkpointer tables (auto-created)

## Key Patterns

1. **Agent Creation**: `create_deep_agent()` with `CopilotKitMiddleware()` + `interrupt_on`
2. **Subagents**: onboarding-agent, job-search-agent, coaching-agent
3. **Tools**: `@tool(args_schema=PydanticModel)`, accept optional `user_id` for persistence
4. **HITL**: `interrupt_on` dict marks tools requiring user confirmation
5. **Checkpointer**: `AsyncPostgresSaver` persists conversations across restarts
6. **Memory**: Zep stores cross-session facts and preferences
7. **Auth**: `NeonAuthUIProvider` wraps app, `authClient.useSession()` gets user
8. **State Sync**: `useCopilotReadable()` passes `user_id` + onboarding state to agent

## Auth Flow

1. User visits `/auth/sign-in` or `/auth/sign-up`
2. Neon Auth handles email OTP verification
3. Session stored, `UserButton` shows in header
4. `authClient.useSession()` provides `user.id`
5. `useCopilotReadable` passes `user_id` to agent
6. Tools persist to `user_profiles` table when `user_id` present

## Tools Summary

### Onboarding Tools (6)

| Tool | Description | HITL |
|------|-------------|------|
| `get_profile_status` | Check user's onboarding progress | No |
| `confirm_role_preference` | Set C-level role (CTO, CFO, etc.) | Yes |
| `confirm_trinity` | Set engagement type (Fractional, Interim, Advisory) | Yes |
| `confirm_experience` | Set years and industries | Yes |
| `confirm_location` | Set location and remote preference | Yes |
| `confirm_search_prefs` | Set day rate and availability | Yes |
| `complete_onboarding` | Finalize onboarding | Yes |

### Job Search Tools (6)

| Tool | Description | HITL |
|------|-------------|------|
| `search_jobs` | Search jobs with filters | No |
| `match_jobs` | Find jobs matching user profile | No |
| `save_job` | Save a job to user's list | Yes |
| `get_saved_jobs` | Get user's saved jobs | No |
| `update_job_status` | Update job status | Yes |
| `get_job_details` | Get full job details | No |

### Coaching Tools (5)

| Tool | Description | HITL |
|------|-------------|------|
| `find_coaches` | Search coaches by specialty/industry | No |
| `get_coach_details` | Get full coach profile | No |
| `schedule_session` | Book a coaching session | Yes |
| `get_my_sessions` | Get user's coaching sessions | No |
| `cancel_session` | Cancel an upcoming session | Yes |

### Memory Tools (3)

| Tool | Description | HITL |
|------|-------------|------|
| `get_user_memory` | Retrieve Zep facts/preferences | No |
| `save_user_preference` | Store a preference to Zep | Yes |
| `save_user_fact` | Store a fact to Zep | Yes |

## Database Migrations

Run migrations against Neon:
```bash
# In Neon SQL Editor or via psql
\i agent/migrations/002_create_jobs_tables.sql
\i agent/migrations/003_create_coaching_tables.sql
```

## Voice Integration

The VoiceInput component provides Hume EVI voice chat:
- Fetches OAuth2 token from `/api/hume-token`
- Connects to Hume on button click
- Forwards voice messages to CopilotKit chat
- Shows connection status and errors

## Next Steps (Phase 4)

**Immediate:**
1. Run coaching migration 003 on Neon (manual SQL - see RESTART_PROMPT.md)
2. Test full flow: Onboarding → Job Search → Coaching
3. Verify voice + chat show same conversation

**Short-term:**
4. Add more realistic jobs seed data
5. Profile editing UI
6. Job application status tracking

**Medium-term:**
7. Job matching algorithm
8. Coach availability calendar
9. Push notifications

See RESTART_PROMPT.md for full Phase 4 todo list.
