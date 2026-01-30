# Deep Fractional - Comprehensive Project Guide

## What Is This Project?

**Deep Fractional** is a production AI career platform for fractional executives (CTO, CFO, CMO, COO, CPO) to find fractional, interim, and advisory roles through conversational AI with voice support.

**Repository:** https://github.com/Londondannyboy/deep-fractional.quest
**Live Frontend:** https://deep-fractional-web.vercel.app
**Live Agent:** https://agent-production-ccb0.up.railway.app

---

## Why This Architecture? (Christian Bromann's Patterns)

This project implements production-ready AI agent patterns from **Christian Bromann**, a LangChain Engineer who wrote the definitive guide on building frontends for LangGraph Deep Agents with CopilotKit.

**Reference Article:** https://dev.to/copilotkit/how-to-build-a-frontend-for-langchain-deep-agents-with-copilotkit-52kd

**Key principles we're following:**

1. **Deep Agents over manual StateGraph** - Use `create_deep_agent()` which handles orchestration automatically
2. **Human-in-the-Loop (HITL)** - Users must confirm before data persists (with countdown timers)
3. **Middleware for safety** - Summarization (token reduction), Tool Call Limits (prevent runaway costs)
4. **State sync via AG-UI** - CopilotKit's protocol for real-time frontend updates
5. **Checkpointing** - PostgreSQL persistence for conversation continuity
6. **Memory separation** - Confirmed data (Neon) vs mentioned facts (Zep)

---

## Project Structure

```
deep-fractional.quest/
├── CLAUDE.md              # THIS FILE - project guide for Claude sessions
├── RESTART_PROMPT.md      # Detailed session continuity (code changes, next steps)
├── docs/
│   ├── PRD.md             # Product requirements, validation values
│   ├── ARCHITECTURE.md    # System design details
│   └── ARTICLE_BREAKDOWN.md # Christian's patterns reference
├── agent/                 # Python backend (Railway)
│   ├── agent.py           # Deep Agents orchestrator + 3 subagents
│   ├── state.py           # TypedDict state schemas
│   ├── main.py            # FastAPI entrypoint
│   ├── tools/             # 20 tools across 4 categories
│   └── persistence/       # Neon client, checkpointer
└── frontend/              # Next.js 15 (Vercel)
    ├── src/app/           # Pages and API routes
    └── src/components/    # UI components (VoiceInput, HITLCard, etc.)
```

---

## Document Hierarchy

| Document | When to Read | What It Contains |
|----------|--------------|------------------|
| **CLAUDE.md** (this) | Every session start | Project overview, architecture, quick reference |
| **RESTART_PROMPT.md** | Continuing Phase 4 work | Detailed session progress, code snippets, next steps |
| **docs/PRD.md** | Understanding requirements | User journey, validation values, tool schemas |
| **docs/ARCHITECTURE.md** | Deep technical context | Component diagrams, data flows |

---

## Current Status

### Phase Progress

| Phase | Status | What It Covers |
|-------|--------|----------------|
| Phase 1 | COMPLETE | Core agent deployed to production |
| Phase 2.1 | COMPLETE | Pydantic schemas on all tools |
| Phase 2.2 | COMPLETE | HITL confirmation flow (11 hooks) |
| Phase 2.3 | COMPLETE | Neon PostgreSQL persistence |
| Phase 2.4 | COMPLETE | Neon Auth (Google OAuth + Email OTP) |
| Phase 2.5 | COMPLETE | Job Search Agent (6 tools) |
| Phase 2.6 | COMPLETE | Coaching Agent (5 tools, needs DB migration) |
| Phase 2.7 | COMPLETE | PostgreSQL Checkpointer |
| Phase 3 | COMPLETE | Hume EVI Voice integration |
| **Phase 4** | **COMPLETE** | Full Voice/Chat/State Integration |
| **Phase 5** | **COMPLETE (98%)** | Tavily Hybrid Job Search |

**Assessment Score: 9/10** against Christian's production patterns

### Phase 4 Complete - All Core Features

- Voice + User Identity flow (user_id flows from Neon Auth -> Hume -> Agent)
- Google OAuth added to Neon Auth
- Voice to CopilotKit message sync fixed
- Zep context integration (voice gets user memory)
- HITLCard component with countdown timer, pause on hover, auto-cancel
- ProfileSidebar component (shows confirmed DB state)
- Summarization Middleware (built-in to deepagents)
- Tool Call Limit Middleware (50 calls max, warns at 80%)
- Voice/Chat context sharing via CopilotWrapper threadId
- All 11 HITL hooks use HITLCard consistently

### Phase 5 Complete - Tavily Hybrid Search

- `hybrid_search_jobs` tool: DB first (free), then Tavily (fresh)
- Auto-saves Tavily results to database for future queries
- Filters out job board aggregators (LinkedIn, Indeed, etc.)
- CopilotKit prompt pattern: never output jobs in chat, only via tools
- Database schema: `jobs` and `saved_jobs` tables

**Requires manual setup:**
1. Add `TAVILY_API_KEY` to Railway environment
2. Run database migration in Neon SQL Editor

### Optional Enhancements (Nice-to-Have)

- `useCoAgentStateRender` for intermediate state visualization
- `useLangGraphInterrupt` for custom interrupts
- Voice HITL announcements (audio cues)

**See `RESTART_PROMPT.md` for testing guide and comparison analysis.**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel - Next.js 15)                  │
│                                                                         │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐       │
│  │  CopilotChat    │   │   VoiceInput    │   │   NeonAuthUI    │       │
│  │  (sidebar)      │   │   (Hume EVI)    │   │ (Google OAuth)  │       │
│  │                 │   │                 │   │                 │       │
│  │ useHumanInTheLoop   │ Zep context     │   │ useSession()    │       │
│  │ ProfileSidebar  │   │ appendMessage() │   │                 │       │
│  │ HITLCard        │   │                 │   │                 │       │
│  └────────┬────────┘   └────────┬────────┘   └────────┬────────┘       │
│           │                     │                      │                │
│           ▼                     ▼                      │                │
│  ┌─────────────────┐   ┌─────────────────┐            │                │
│  │ /api/copilotkit │   │ /api/hume-token │            │                │
│  │ /api/zep-context│   │ /api/chat/completions (CLM)  │                │
│  └────────┬────────┘   └─────────────────┘            │                │
└───────────┼───────────────────────────────────────────┼────────────────┘
            │                                           │
            ▼                                           ▼
┌───────────────────────────────────────┐   ┌───────────────────────────┐
│     DeepAgents (Railway - FastAPI)    │   │    Neon PostgreSQL        │
│                                       │   │                           │
│  ┌─────────────────────────────────┐  │   │  user_profiles (confirmed)│
│  │         ORCHESTRATOR            │  │   │  jobs                     │
│  │   (routes to subagents)         │  │   │  saved_jobs               │
│  │   user_id at state top level    │  │   │  coaches                  │
│  └─────────────┬───────────────────┘  │   │  coaching_sessions        │
│                │                      │   │  checkpoint_* (auto)      │
│   ┌────────────┼────────────┐        │   │  neon_auth.* (auto)       │
│   ▼            ▼            ▼        │   └───────────────────────────┘
│ ┌─────┐    ┌─────┐    ┌─────────┐   │
│ │Onb. │    │Jobs │    │Coaching │   │   ┌───────────────────────────┐
│ │Agent│    │Agent│    │Agent    │   │   │      Zep Cloud            │
│ └──┬──┘    └──┬──┘    └────┬────┘   │   │  (cross-session memory)   │
│    │          │            │         │   │  (mentioned facts)        │
│    ▼          ▼            ▼         │   └───────────────────────────┘
│  6 tools    6 tools     5 tools      │
│  + HITL     + HITL      + HITL       │   ┌───────────────────────────┐
│                                       │   │     Hume EVI Cloud        │
│  CopilotKitMiddleware                │◄──│   (voice interface)       │
│  AsyncPostgresSaver (checkpointer)   │   └───────────────────────────┘
│  Gemini 2.0 Flash                    │
└───────────────────────────────────────┘
```

### Data Architecture

| Storage | Purpose | Example |
|---------|---------|---------|
| **Neon PostgreSQL** | Confirmed data (HITL-approved) | User confirms "CTO" role → saved to `user_profiles` |
| **Zep Cloud** | Mentioned facts (conversation context) | User says "I'm interested in fintech" → stored in Zep graph |

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Agent Framework | LangChain Deep Agents | `create_deep_agent()` with subagents |
| State Sync | CopilotKit AG-UI | Real-time frontend updates |
| LLM | Gemini 2.0 Flash | Fast, capable, cost-effective |
| Database | Neon PostgreSQL | Confirmed user data |
| Auth | Neon Auth | Google OAuth + Email OTP |
| Checkpointer | AsyncPostgresSaver | Conversation persistence |
| Memory | Zep Cloud | Cross-session facts/preferences |
| Voice | Hume EVI | Emotional voice interface |
| Backend | FastAPI + uvicorn | Python agent server |
| Frontend | Next.js 15 + React 19 | Modern React with App Router |
| Deploy | Railway + Vercel | Agent + Frontend hosting |

---

## Key Patterns

### 1. Deep Agents Creation
```python
# agent/agent.py
agent_graph = create_deep_agent(
    model=llm,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=all_tools,
    subagents=[onboarding_agent, job_search_agent, coaching_agent],
    middleware=[CopilotKitMiddleware()],
    checkpointer=AsyncPostgresSaver(pool),
    interrupt_on={"confirm_role_preference": True, ...}  # HITL tools
)
```

### 2. HITL with Countdown Timer
```typescript
// frontend/src/components/HITLCard.tsx
<HITLCard
  title="Confirm Role"
  description="Save CTO as your target role?"
  onConfirm={() => resolve("confirmed")}
  onCancel={() => resolve("rejected")}
  countdownSeconds={15}
  autoAction="cancel"  // Auto-cancels if no response
/>
```

### 3. User Identity Flow
```
Neon Auth (Google) → useSession() → useCopilotReadable({ user_id })
                                           ↓
Voice: Hume EVI → customSessionId includes userId → CLM endpoint extracts it
                                           ↓
Agent: state.user_id at top level → tools use it for persistence
```

### 4. State Sync
```typescript
// Frontend passes state to agent
useCopilotReadable({
  description: "Current user and onboarding state",
  value: { user_id, onboarding }
});

// Frontend visualizes confirmed state
<ProfileSidebar onboarding={onboarding} userName={name} userId={id} />
```

---

## Tools Summary

| Category | Tools | HITL Tools |
|----------|-------|------------|
| Onboarding | 6 | 5 (confirm_role, confirm_trinity, etc.) |
| Job Search | 6 | 2 (save_job, update_job_status) |
| Coaching | 5 | 2 (schedule_session, cancel_session) |
| Memory | 3 | 2 (save_preference, save_fact) |
| **Total** | **20** | **11** |

---

## Environment Variables

### Railway (agent)
```bash
GOOGLE_API_KEY=<Gemini API key>
GOOGLE_MODEL=gemini-2.0-flash
DATABASE_URL=<Neon PostgreSQL connection string>
ZEP_API_KEY=<Zep Cloud API key>
ZEP_GRAPH=fractional-jobs-graph
```

### Vercel (frontend)
```bash
LANGGRAPH_DEPLOYMENT_URL=https://agent-production-ccb0.up.railway.app
NEON_AUTH_BASE_URL=<Neon Auth endpoint>
HUME_API_KEY=<Hume API key>
HUME_SECRET_KEY=<Hume secret key>
NEXT_PUBLIC_HUME_CONFIG_ID=5900eabb-8de1-42cf-ba18-3a718257b3e7
ZEP_API_KEY=<Zep Cloud API key>
ZEP_GRAPH=fractional-jobs-graph
```

---

## Quick Commands

```bash
# Local development
cd agent && uv run python main.py    # Agent on :8123
cd frontend && npm run dev           # Frontend on :3000

# Deploy (auto via GitHub)
git add -A && git commit -m "message" && git push origin main

# Neon SQL Editor (for migrations)
# https://console.neon.tech/app/projects/sweet-hat-02969611/sql-editor
```

---

## Session Continuity

**For detailed implementation progress and code examples from the January 30, 2026 session, read `RESTART_PROMPT.md`.**

It contains:
- Completed items with file changes
- Code snippets for key changes (Voice+Identity, message sync, Zep context)
- Architecture clarifications
- Next steps with implementation examples for middleware
- Git commit history

---

## Files Quick Reference

### Most Important Files

| File | What It Does |
|------|--------------|
| `agent/agent.py` | Deep Agents orchestrator, 3 subagents, middleware |
| `agent/state.py` | State schema with user_id at top level |
| `frontend/src/app/page.tsx` | Main UI, 11 HITL hooks, ProfileSidebar |
| `frontend/src/components/VoiceInput.tsx` | Hume EVI voice with Zep context |
| `frontend/src/components/HITLCard.tsx` | Countdown timer confirmation card |
| `frontend/src/app/api/chat/completions/route.ts` | CLM endpoint (voice → agent) |

### New Components (Phase 4)

| File | Purpose |
|------|---------|
| `HITLCard.tsx` | Reusable HITL with 15s countdown, pause on hover |
| `ProfileSidebar.tsx` | Shows confirmed DB state with progress |
| `providers.tsx` | NeonAuthUIProvider with Google OAuth |
| `api/zep-context/route.ts` | Fetches Zep memory for voice prompts |

---

*Last updated: January 30, 2026 - Phase 5 Complete (98%) - Tavily hybrid search + all Christian patterns*
