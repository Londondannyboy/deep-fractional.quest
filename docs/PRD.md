# Product Requirements: Fractional Quest

## Overview

Fractional Quest helps fractional executives (CTO, CFO, CMO, COO, CPO) find fractional, interim, and advisory roles.

## Current Status

- **Phase 1**: COMPLETE - Core agent deployed to production
- **Phase 2.1**: COMPLETE - Pydantic schemas on all tools
- **Phase 2.2**: COMPLETE - HITL confirmation flow (11 hooks)
- **Phase 2.3**: COMPLETE - Neon Persistence
- **Phase 2.4**: COMPLETE - Neon Auth (email OTP)
- **Phase 2.5**: COMPLETE - Job Search Agent (6 tools)
- **Phase 2.6**: COMPLETE (code) - Coaching Agent (DB migration needed)
- **Phase 2.7**: COMPLETE - PostgreSQL Checkpointer
- **Phase 3**: COMPLETE - Hume EVI Voice integration
- **Phase 4**: IN PROGRESS - Voice + User Identity + Christian's patterns

## Production URLs

- **Frontend**: https://deep-fractional-web.vercel.app
- **Agent**: https://agent-production-ccb0.up.railway.app
- **Database**: Neon PostgreSQL (eu-west-2)

## User Journey

### 1. Onboarding (6 Steps) - COMPLETE

| Step | Question | Tool | Pydantic Schema |
|------|----------|------|-----------------|
| 1 | What C-level role are you seeking? | `confirm_role_preference` | RolePreferenceInput |
| 2 | Fractional, Interim, or Advisory? | `confirm_trinity` | TrinityInput |
| 3 | Years of experience and industries? | `confirm_experience` | ExperienceInput |
| 4 | Location and remote preferences? | `confirm_location` | LocationInput |
| 5 | Compensation expectations? | `confirm_search_prefs` | SearchPrefsInput |
| 6 | Profile complete | `complete_onboarding` | - |

### 2. Job Search (Phase 2.5)

After onboarding, users can:
- Search for matching jobs
- View job recommendations
- Save jobs to their profile

### 3. Coaching (Phase 2.6)

Users can:
- Connect with executive coaches
- Schedule sessions
- Get career guidance

## Tool Specifications

### Validation Values

```python
VALID_ROLES = ["cto", "cfo", "cmo", "coo", "cpo", "other"]
VALID_TRINITY = ["fractional", "interim", "advisory", "open"]
VALID_REMOTE = ["remote", "hybrid", "onsite", "flexible"]
VALID_AVAILABILITY = ["immediately", "1_month", "3_months", "flexible"]
```

### `confirm_role_preference`

```python
class RolePreferenceInput(BaseModel):
    role: str = Field(description="C-level role: cto, cfo, cmo, coo, cpo, other")

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        return v.lower().strip()

@tool(args_schema=RolePreferenceInput)
def confirm_role_preference(role: str) -> Dict[str, Any]:
    """Confirm the C-level role preference."""
```

### `confirm_trinity`

```python
class TrinityInput(BaseModel):
    engagement_type: str = Field(description="Engagement type: fractional, interim, advisory, open")

@tool(args_schema=TrinityInput)
def confirm_trinity(engagement_type: str) -> Dict[str, Any]:
    """Confirm the engagement type preference."""
```

### `confirm_experience`

```python
class ExperienceInput(BaseModel):
    years: int = Field(description="Years of executive experience", ge=0)
    industries: str = Field(description="Comma-separated list of industries")

@tool(args_schema=ExperienceInput)
def confirm_experience(years: int, industries: str) -> Dict[str, Any]:
    """Confirm experience level and industries."""
```

### `confirm_location`

```python
class LocationInput(BaseModel):
    location: str = Field(description="City/country or 'Remote'")
    remote_preference: str = Field(description="One of: remote, hybrid, onsite, flexible")

@tool(args_schema=LocationInput)
def confirm_location(location: str, remote_preference: str) -> Dict[str, Any]:
    """Confirm location and remote work preference."""
```

### `confirm_search_prefs`

```python
class SearchPrefsInput(BaseModel):
    day_rate_min: int = Field(description="Minimum day rate in GBP", ge=0)
    day_rate_max: int = Field(description="Maximum day rate in GBP", ge=0)
    availability: str = Field(description="One of: immediately, 1_month, 3_months, flexible")

@tool(args_schema=SearchPrefsInput)
def confirm_search_prefs(day_rate_min: int, day_rate_max: int, availability: str) -> Dict[str, Any]:
    """Confirm compensation and availability."""
```

### `complete_onboarding`

```python
@tool
def complete_onboarding() -> Dict[str, Any]:
    """Mark onboarding as complete."""
```

## State Schema

```python
from typing import TypedDict, Optional, List

class OnboardingState(TypedDict, total=False):
    current_step: int  # 0-6
    completed: bool
    role_preference: str
    trinity: str
    experience_years: int
    industries: List[str]
    location: str
    remote_preference: str
    day_rate_min: int
    day_rate_max: int
    availability: str

class UserState(TypedDict, total=False):
    user_id: str
    name: str
    email: str

class AgentState(TypedDict, total=False):
    onboarding: OnboardingState
    user: UserState
    active_agent: str
```

## Database Schema (Neon)

```sql
-- User profile items (confirmed preferences)
CREATE TABLE user_profile_items (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    item_type VARCHAR(50) NOT NULL,
    value TEXT NOT NULL,
    confirmed BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, item_type, value)
);

-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    role_type VARCHAR(50),
    engagement_type VARCHAR(50),
    location VARCHAR(255),
    remote_preference VARCHAR(50),
    day_rate_min INT,
    day_rate_max INT,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Saved jobs
CREATE TABLE saved_jobs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    job_id INT REFERENCES jobs(id),
    saved_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, job_id)
);
```

## Authentication (Neon Auth)

Using Neon Auth (built on Better Auth), NOT Clerk.

```typescript
// Frontend auth client
import { createAuthClient } from "@neon/auth-client";

const auth = createAuthClient({
  baseURL: process.env.NEON_AUTH_URL,
});

// Pass to agent
useCopilotReadable({
  description: "Current user",
  value: { userId: user?.id }
});
```

## Success Metrics

1. **Onboarding Completion Rate**: % of users who complete all 6 steps
2. **Time to Complete**: Average time from start to completion
3. **State Sync Reliability**: Tool results correctly update UI
4. **Agent Accuracy**: Correct routing to subagents
5. **HITL Acceptance Rate**: % of tool calls confirmed vs rejected
