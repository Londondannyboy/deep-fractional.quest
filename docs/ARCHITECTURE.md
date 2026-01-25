# Architecture: Multi-Agent Pattern

## Overview

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATOR AGENT                  │
│  create_deep_agent() with CopilotKitMiddleware      │
│  Routes to subagents based on context               │
└──────────────────────┬──────────────────────────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  ONBOARDING  │ │  JOB_SEARCH  │ │   COACHING   │
│  subagent    │ │  subagent    │ │   subagent   │
│              │ │              │ │              │
│ - role pref  │ │ - search     │ │ - find       │
│ - trinity    │ │ - match      │ │ - schedule   │
│ - experience │ │ - save       │ │ - context    │
│ - location   │ │              │ │              │
│ - search     │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Agent Configuration

```python
subagents = [
    {
        "name": "onboarding-agent",
        "description": "Guides users through profile building",
        "system_prompt": ONBOARDING_PROMPT,
        "tools": [
            confirm_role_preference,
            confirm_trinity,
            confirm_experience,
            confirm_location,
            confirm_search_prefs,
            complete_onboarding,
        ],
    },
    {
        "name": "job-search-agent",
        "description": "Finds relevant job opportunities",
        "system_prompt": JOB_SEARCH_PROMPT,
        "tools": [search_jobs, match_jobs, save_job],
    },
    {
        "name": "coaching-agent",
        "description": "Connects users with executive coaches",
        "system_prompt": COACHING_PROMPT,
        "tools": [find_coaches, schedule_session],
    },
]
```

## State Flow

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  useCopilotReadable() ──────────────────────────────────┐   │
│                                                          │   │
│  useDefaultTool() ◄───────────────────────────────────┐ │   │
│       │                                                │ │   │
│       ▼                                                │ │   │
│  [Update UI State]                                     │ │   │
└────────┬──────────────────────────────────────────────┬┴─┴───┘
         │ POST /api/copilotkit                          │
         ▼                                               │
┌─────────────────────────────────────────────────────────────┐
│                    COPILOTKIT RUNTIME                        │
│  LangGraphHttpAgent → Agent Backend                          │
└────────┬────────────────────────────────────────────────────┘
         │ AG-UI Protocol
         ▼
┌─────────────────────────────────────────────────────────────┐
│                      AGENT BACKEND                           │
│  FastAPI + add_langgraph_fastapi_endpoint()                 │
│       │                                                      │
│       ▼                                                      │
│  create_deep_agent() with CopilotKitMiddleware()            │
│       │                                                      │
│       ▼                                                      │
│  [Execute Tools] ──────────────────────────────────────────┐│
│       │                                          Stream     ││
│       ▼                                          Results    ││
│  [Return Dict with state updates] ──────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Routing Logic

The orchestrator routes based on:

1. **Onboarding not complete** → onboarding-agent
2. **Job-related keywords** → job-search-agent
3. **Coaching keywords** → coaching-agent
4. **General questions** → Handle directly

```python
ORCHESTRATOR_PROMPT = """
You are the main orchestrator for Fractional Quest.

Routing Rules:
1. If onboarding is not complete, delegate to onboarding-agent
2. If user asks about jobs/roles/opportunities → job-search-agent
3. If user asks about coaching/mentoring → coaching-agent
4. For general questions, answer directly
"""
```

## Tool Return Pattern

Tools return dicts that become state updates:

```python
@tool
def confirm_role_preference(role: str) -> Dict[str, Any]:
    """Confirm the C-level role preference."""
    return {
        "success": True,
        "role_preference": role.lower(),
        "next_step": "trinity",
        "message": f"Great! I've noted your preference for {role} roles."
    }
```

Frontend captures via `useDefaultTool()`:

```typescript
useDefaultTool({
  render: ({ name, status, result }) => {
    if (name === "confirm_role_preference" && status === "complete") {
      setOnboarding(prev => ({
        ...prev,
        role_preference: result.role_preference
      }));
    }
    // Render tool call UI
  }
});
```

## Persistence Strategy

1. **Checkpointer**: `MemorySaver()` for conversation state
2. **Neon PostgreSQL**: User profiles, jobs, preferences
3. **Tool Results**: Streamed via AG-UI, captured by frontend

## Deployment

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Vercel     │ ──────► │   Railway    │ ──────► │    Neon      │
│   Frontend   │         │   Agent      │         │    DB        │
│   Next.js    │         │   FastAPI    │         │   Postgres   │
└──────────────┘         └──────────────┘         └──────────────┘
```

Environment:
- Vercel: `LANGGRAPH_DEPLOYMENT_URL=https://railway-url.up.railway.app`
- Railway: `GOOGLE_API_KEY`, `DATABASE_URL`
