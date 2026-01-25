"""
State schemas for Fractional Quest agent.

Uses TypedDict for CopilotKit compatibility.
"""

from typing import TypedDict, Optional, List


class OnboardingState(TypedDict, total=False):
    """Tracks onboarding progress."""
    current_step: int  # 0-5
    completed: bool

    # Step 1: Role preference
    role_preference: str  # cto, cfo, cmo, coo, cpo, other

    # Step 2: Engagement type
    trinity: str  # fractional, interim, advisory, open

    # Step 3: Experience
    experience_years: int
    industries: List[str]

    # Step 4: Location
    location: str
    remote_preference: str  # remote, hybrid, onsite, flexible

    # Step 5: Search preferences
    day_rate_min: int
    day_rate_max: int
    availability: str  # immediately, 1_month, 3_months, flexible


class UserState(TypedDict, total=False):
    """User identity (from auth, future)."""
    user_id: str
    name: str
    email: str


class PageContext(TypedDict, total=False):
    """Current page context."""
    current_page: str
    page_type: str


class AgentState(TypedDict, total=False):
    """
    Main agent state.

    Extends with CopilotKit state fields automatically
    via CopilotKitMiddleware.
    """
    onboarding: OnboardingState
    user: UserState
    page_context: PageContext
    active_agent: Optional[str]  # Current subagent handling request
