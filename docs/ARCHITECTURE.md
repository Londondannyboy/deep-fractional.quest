# Architecture: Multi-Agent Pattern

## Overview

```
┌─────────────────────────────────────────────────────────┐
│                    USER (Authenticated)                  │
└─────────────────────────────────────────────────────────┘
                           │
                    Neon Auth (Better Auth)
                           │
┌─────────────────────────────────────────────────────────┐
│                  VERCEL FRONTEND                         │
│  https://deep-fractional-web.vercel.app                 │
│  - CopilotKit provider                                  │
│  - useDefaultTool (tool capture + HITL)                 │
│  - useCopilotReadable (user context)                    │
└─────────────────────────────────────────────────────────┘
                           │
                    AG-UI Protocol
                           │
┌─────────────────────────────────────────────────────────┐
│                  RAILWAY AGENT                           │
│  https://agent-production-ccb0.up.railway.app           │
│  create_deep_agent() + CopilotKitMiddleware             │
│  + interrupt_before (HITL)                              │
│                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ ONBOARDING  │ │ JOB_SEARCH  │ │  COACHING   │       │
│  │  subagent   │ │  subagent   │ │  subagent   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────┘
                           │
                    asyncpg
                           │
┌─────────────────────────────────────────────────────────┐
│                     NEON DATABASE                        │
│  ep-divine-waterfall-abig6fic-pooler.eu-west-2.aws.neon │
│  - user_profile_items (profiles)                        │
│  - jobs (job listings)                                  │
│  - sessions (coaching)                                  │
└─────────────────────────────────────────────────────────┘
```

## Agent Configuration

```python
from deepagents import create_deep_agent, CopilotKitMiddleware
from langgraph.checkpoint.memory import MemorySaver

subagents = [
    {
        "name": "onboarding-agent",
        "description": "Guides users through profile building",
        "system_prompt": ONBOARDING_PROMPT,
        "tools": [
            confirm_role_preference,  # with RolePreferenceInput schema
            confirm_trinity,          # with TrinityInput schema
            confirm_experience,       # with ExperienceInput schema
            confirm_location,         # with LocationInput schema
            confirm_search_prefs,     # with SearchPrefsInput schema
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

agent_graph = create_deep_agent(
    model=llm,
    system_prompt=ORCHESTRATOR_PROMPT,
    tools=[],  # orchestrator delegates to subagents
    subagents=subagents,
    middleware=[CopilotKitMiddleware()],
    checkpointer=MemorySaver(),
    interrupt_before=["tools"],  # HITL confirmation
)
```

## Tool Pattern with Pydantic Schema

```python
from pydantic import BaseModel, Field, field_validator
from langchain.tools import tool

class RolePreferenceInput(BaseModel):
    """Input schema for confirm_role_preference tool."""
    role: str = Field(description="C-level role: cto, cfo, cmo, coo, cpo, other")

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        return v.lower().strip()

@tool(args_schema=RolePreferenceInput)
def confirm_role_preference(role: str) -> Dict[str, Any]:
    """Confirm the C-level role preference."""
    if role not in VALID_ROLES:
        return {"success": False, "error": "Invalid role"}
    return {
        "success": True,
        "role_preference": role,
        "next_step": "trinity",
        "message": f"Great! I've noted your preference for {role.upper()} roles."
    }
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

## Frontend Tool Capture

```typescript
useDefaultTool({
  render: ({ name, status, result, args }) => {
    // HITL: Handle confirmation requests
    if (status === "awaiting_confirmation") {
      return (
        <ConfirmationCard
          tool={name}
          args={args}
          onConfirm={() => /* resume graph */}
          onReject={() => /* cancel */}
        />
      );
    }

    // Capture completed tool results
    if (status === "complete" && result?.success) {
      // Update local state with tool result
      setOnboarding(prev => ({ ...prev, ...result }));
    }

    return <ToolCallCard name={name} result={result} />;
  }
});
```

## Routing Logic

The orchestrator routes based on:

1. **Onboarding not complete** → onboarding-agent
2. **Job-related keywords** → job-search-agent
3. **Coaching keywords** → coaching-agent
4. **General questions** → Handle directly

## Persistence Strategy

1. **Checkpointer**: `MemorySaver()` for conversation state
2. **Neon PostgreSQL**: User profiles, jobs, preferences
3. **Tool Results**: Streamed via AG-UI, captured by frontend

## Environment Variables

**Railway (Agent):**
```
GOOGLE_API_KEY=...
DATABASE_URL=postgresql://neondb_owner:npg_h4SxyI8GrpzN@ep-divine-waterfall-abig6fic-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require
PORT=8123  # Railway sets this automatically
```

**Vercel (Frontend):**
```
LANGGRAPH_DEPLOYMENT_URL=https://agent-production-ccb0.up.railway.app
```
