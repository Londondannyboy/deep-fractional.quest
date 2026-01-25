# Product Requirements: Fractional Quest

## Overview

Fractional Quest helps fractional executives (CTO, CFO, CMO, COO, CPO) find fractional, interim, and advisory roles.

## User Journey

### 1. Onboarding (6 Steps)

| Step | Question | Tool |
|------|----------|------|
| 1 | What C-level role are you seeking? | `confirm_role_preference` |
| 2 | Fractional, Interim, or Advisory? | `confirm_trinity` |
| 3 | Years of experience and industries? | `confirm_experience` |
| 4 | Location and remote preferences? | `confirm_location` |
| 5 | Compensation expectations? | `confirm_search_prefs` |
| 6 | Profile complete | `complete_onboarding` |

### 2. Job Search

After onboarding, users can:
- Search for matching jobs
- View job recommendations
- Save jobs to their profile

### 3. Coaching

Users can:
- Connect with executive coaches
- Schedule sessions
- Get career guidance

## Onboarding Tool Specifications

### `confirm_role_preference`

```python
@tool
def confirm_role_preference(role: str) -> Dict[str, Any]:
    """
    Confirm the C-level role preference.

    Args:
        role: One of cto, cfo, cmo, coo, cpo, other

    Returns:
        success, role_preference, next_step
    """
```

Valid roles: `cto`, `cfo`, `cmo`, `coo`, `cpo`, `other`

### `confirm_trinity`

```python
@tool
def confirm_trinity(engagement_type: str) -> Dict[str, Any]:
    """
    Confirm the engagement type preference.

    Args:
        engagement_type: One of fractional, interim, advisory, open

    Returns:
        success, trinity, next_step
    """
```

Valid types: `fractional`, `interim`, `advisory`, `open`

### `confirm_experience`

```python
@tool
def confirm_experience(years: int, industries: str) -> Dict[str, Any]:
    """
    Confirm experience level and industries.

    Args:
        years: Years of executive experience
        industries: Comma-separated list of industries

    Returns:
        success, experience, industries, next_step
    """
```

### `confirm_location`

```python
@tool
def confirm_location(location: str, remote_preference: str) -> Dict[str, Any]:
    """
    Confirm location and remote work preference.

    Args:
        location: City, country or "Remote"
        remote_preference: One of remote, hybrid, onsite, flexible

    Returns:
        success, location, remote_preference, next_step
    """
```

### `confirm_search_prefs`

```python
@tool
def confirm_search_prefs(
    day_rate_min: int,
    day_rate_max: int,
    availability: str
) -> Dict[str, Any]:
    """
    Confirm compensation and availability.

    Args:
        day_rate_min: Minimum day rate in GBP
        day_rate_max: Maximum day rate in GBP
        availability: One of immediately, 1_month, 3_months, flexible

    Returns:
        success, day_rate_range, availability, next_step
    """
```

### `complete_onboarding`

```python
@tool
def complete_onboarding() -> Dict[str, Any]:
    """
    Mark onboarding as complete and summarize profile.

    Returns:
        success, completed, profile_summary
    """
```

## State Schema

```python
from typing import TypedDict, Optional, List

class OnboardingState(TypedDict, total=False):
    current_step: int  # 0-5
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

## UI Components

### Onboarding Progress

Display current step and completed fields:

```tsx
function OnboardingProgress({ onboarding }) {
  const steps = [
    { key: 'role_preference', label: 'Role' },
    { key: 'trinity', label: 'Type' },
    { key: 'experience', label: 'Experience' },
    { key: 'location', label: 'Location' },
    { key: 'search_prefs', label: 'Preferences' },
  ];

  return (
    <div className="steps">
      {steps.map((step, i) => (
        <Step
          key={step.key}
          active={onboarding.current_step === i}
          completed={onboarding[step.key] !== undefined}
        >
          {step.label}
        </Step>
      ))}
    </div>
  );
}
```

### Profile Card

Display confirmed information:

```tsx
function ProfileCard({ onboarding }) {
  return (
    <Card>
      <ProfileItem label="Role" value={onboarding.role_preference} />
      <ProfileItem label="Type" value={onboarding.trinity} />
      <ProfileItem label="Experience" value={`${onboarding.experience_years} years`} />
      <ProfileItem label="Location" value={onboarding.location} />
      <ProfileItem label="Rate" value={`£${onboarding.day_rate_min}-${onboarding.day_rate_max}/day`} />
    </Card>
  );
}
```

## Success Metrics

1. **Onboarding Completion Rate**: % of users who complete all 6 steps
2. **Time to Complete**: Average time from start to completion
3. **State Sync Reliability**: Tool results correctly update UI
4. **Agent Accuracy**: Correct routing to subagents
