"""
Onboarding tools for Fractional Quest.

Each tool confirms a piece of user profile information
and returns state updates that sync to the frontend.

Uses Pydantic schemas for input validation (args_schema).
Persists to Neon PostgreSQL when user_id is provided.

IMPORTANT: Tools are async and AWAIT database writes to prevent race conditions.
"""

from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Literal, Optional

# Persistence helper (lazy import to avoid startup issues)
_neon_client = None


def _get_neon_client():
    """Lazy load Neon client to avoid import errors if not configured."""
    global _neon_client
    if _neon_client is None:
        try:
            from persistence.neon import get_neon_client
            _neon_client = get_neon_client()
        except Exception as e:
            print(f"[TOOLS] Neon client not available: {e}")
            return None
    return _neon_client


# Valid values for validation
VALID_ROLES = ["cto", "cfo", "cmo", "coo", "cpo", "other"]
VALID_TRINITY = ["fractional", "interim", "advisory", "open"]
VALID_REMOTE = ["remote", "hybrid", "onsite", "flexible"]
VALID_AVAILABILITY = ["immediately", "1_month", "3_months", "flexible"]


# =============================================================================
# Pydantic Input Schemas
# =============================================================================

class RolePreferenceInput(BaseModel):
    """Input schema for confirm_role_preference tool."""
    role: str = Field(
        description="C-level role type: cto, cfo, cmo, coo, cpo, or other"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        return v.lower().strip()


class TrinityInput(BaseModel):
    """Input schema for confirm_trinity tool."""
    engagement_type: str = Field(
        description="Engagement type: fractional, interim, advisory, or open"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )

    @field_validator("engagement_type")
    @classmethod
    def normalize_type(cls, v: str) -> str:
        return v.lower().strip()


class ExperienceInput(BaseModel):
    """Input schema for confirm_experience tool."""
    years: int = Field(
        description="Years of executive experience",
        ge=0  # greater than or equal to 0
    )
    industries: str = Field(
        description="Comma-separated list of industries (e.g., 'Tech, Finance, Gaming')"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )


class LocationInput(BaseModel):
    """Input schema for confirm_location tool."""
    location: str = Field(
        description="City/country (e.g., 'London', 'New York', 'Remote')"
    )
    remote_preference: str = Field(
        description="Remote work preference: remote, hybrid, onsite, or flexible"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )

    @field_validator("remote_preference")
    @classmethod
    def normalize_remote(cls, v: str) -> str:
        return v.lower().strip()


class SearchPrefsInput(BaseModel):
    """Input schema for confirm_search_prefs tool."""
    day_rate_min: int = Field(
        description="Minimum day rate in GBP",
        ge=0
    )
    day_rate_max: int = Field(
        description="Maximum day rate in GBP",
        ge=0
    )
    availability: str = Field(
        description="Availability: immediately, 1_month, 3_months, or flexible"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )

    @field_validator("availability")
    @classmethod
    def normalize_availability(cls, v: str) -> str:
        return v.lower().strip()


class CompleteOnboardingInput(BaseModel):
    """Input schema for complete_onboarding tool."""
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for persistence (from authenticated session)"
    )


# =============================================================================
# Profile Status Tool (for workflow routing)
# =============================================================================

class GetProfileStatusInput(BaseModel):
    """Input schema for get_profile_status tool."""
    user_id: str = Field(description="The user's unique identifier")


@tool(args_schema=GetProfileStatusInput)
async def get_profile_status(user_id: str) -> Dict[str, Any]:
    """
    Get the user's current profile and onboarding status from the database.

    Use this at the START of each conversation to determine:
    - If the user is new or returning
    - What onboarding step they're on (if incomplete)
    - What preferences they've already set

    Args:
        user_id: The user's unique identifier

    Returns:
        Profile status including onboarding_completed flag and all saved preferences
    """
    client = _get_neon_client()
    if not client:
        return {
            "success": False,
            "is_new_user": True,
            "onboarding_completed": False,
            "current_step": 0,
            "profile": {},
            "message": "Database not available - treat as new user",
        }

    try:
        profile = await client.get_profile(user_id)

        if not profile:
            return {
                "success": True,
                "is_new_user": True,
                "onboarding_completed": False,
                "current_step": 0,
                "profile": {},
                "message": "New user - start onboarding",
            }

        # Determine current step based on what's filled
        current_step = 0
        if profile.get("role_preference"):
            current_step = 1
        if profile.get("trinity"):
            current_step = 2
        if profile.get("experience_years") is not None:
            current_step = 3
        if profile.get("location"):
            current_step = 4
        if profile.get("day_rate_min") is not None:
            current_step = 5
        if profile.get("onboarding_completed"):
            current_step = 6

        return {
            "success": True,
            "is_new_user": False,
            "onboarding_completed": bool(profile.get("onboarding_completed", False)),
            "current_step": current_step,
            "profile": {
                "role_preference": profile.get("role_preference"),
                "trinity": profile.get("trinity"),
                "experience_years": profile.get("experience_years"),
                "industries": profile.get("industries", []),
                "location": profile.get("location"),
                "remote_preference": profile.get("remote_preference"),
                "day_rate_min": profile.get("day_rate_min"),
                "day_rate_max": profile.get("day_rate_max"),
                "availability": profile.get("availability"),
            },
            "message": "Onboarding complete - ready for job search" if profile.get("onboarding_completed") else f"Resume onboarding at step {current_step + 1}",
        }

    except Exception as e:
        print(f"[TOOLS] Error getting profile status: {e}")
        return {
            "success": False,
            "is_new_user": True,
            "onboarding_completed": False,
            "current_step": 0,
            "profile": {},
            "message": f"Error reading profile: {str(e)}",
        }


# =============================================================================
# Tools with Pydantic Schemas
# =============================================================================

@tool(args_schema=RolePreferenceInput)
async def confirm_role_preference(role: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Confirm the C-level role preference.

    Args:
        role: The role type (cto, cfo, cmo, coo, cpo, or other)
        user_id: Optional user ID for persistence

    Returns:
        State update with role_preference and next step
    """
    normalized = role.lower().strip()

    if normalized not in VALID_ROLES:
        return {
            "success": False,
            "error": f"Invalid role. Please choose from: {', '.join(VALID_ROLES)}",
        }

    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.update_role_preference(user_id, normalized)
                print(f"[TOOLS] Persisted role_preference={normalized} for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to persist role_preference: {e}")

    return {
        "success": True,
        "role_preference": normalized,
        "current_step": 1,
        "next_step": "trinity",
        "message": f"Great! I've noted your preference for {normalized.upper()} roles.",
    }


@tool(args_schema=TrinityInput)
async def confirm_trinity(engagement_type: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Confirm the engagement type preference (fractional/interim/advisory).

    Args:
        engagement_type: One of fractional, interim, advisory, or open
        user_id: Optional user ID for persistence

    Returns:
        State update with trinity and next step
    """
    normalized = engagement_type.lower().strip()

    if normalized not in VALID_TRINITY:
        return {
            "success": False,
            "error": f"Invalid type. Please choose from: {', '.join(VALID_TRINITY)}",
        }

    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.update_trinity(user_id, normalized)
                print(f"[TOOLS] Persisted trinity={normalized} for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to persist trinity: {e}")

    return {
        "success": True,
        "trinity": normalized,
        "current_step": 2,
        "next_step": "experience",
        "message": f"Perfect! You're looking for {normalized} opportunities.",
    }


@tool(args_schema=ExperienceInput)
async def confirm_experience(years: int, industries: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Confirm experience level and industries.

    Args:
        years: Years of executive experience
        industries: Comma-separated list of industries
        user_id: Optional user ID for persistence

    Returns:
        State update with experience and industries
    """
    if years < 0:
        return {
            "success": False,
            "error": "Years of experience must be positive.",
        }

    industry_list = [i.strip() for i in industries.split(",") if i.strip()]

    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.update_experience(user_id, years, industry_list)
                print(f"[TOOLS] Persisted experience={years}yrs, industries={industry_list} for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to persist experience: {e}")

    return {
        "success": True,
        "experience_years": years,
        "industries": industry_list,
        "current_step": 3,
        "next_step": "location",
        "message": f"Got it! {years} years across {', '.join(industry_list)}.",
    }


@tool(args_schema=LocationInput)
async def confirm_location(location: str, remote_preference: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Confirm location and remote work preference.

    Args:
        location: City/country or "Remote"
        remote_preference: One of remote, hybrid, onsite, flexible
        user_id: Optional user ID for persistence

    Returns:
        State update with location info
    """
    remote_norm = remote_preference.lower().strip()

    if remote_norm not in VALID_REMOTE:
        return {
            "success": False,
            "error": f"Invalid preference. Choose from: {', '.join(VALID_REMOTE)}",
        }

    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.update_location(user_id, location.strip(), remote_norm)
                print(f"[TOOLS] Persisted location={location}, remote={remote_norm} for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to persist location: {e}")

    return {
        "success": True,
        "location": location.strip(),
        "remote_preference": remote_norm,
        "current_step": 4,
        "next_step": "search_prefs",
        "message": f"Location: {location}, preference: {remote_norm}.",
    }


@tool(args_schema=SearchPrefsInput)
async def confirm_search_prefs(
    day_rate_min: int,
    day_rate_max: int,
    availability: str,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Confirm compensation and availability.

    Args:
        day_rate_min: Minimum day rate in GBP
        day_rate_max: Maximum day rate in GBP
        availability: One of immediately, 1_month, 3_months, flexible
        user_id: Optional user ID for persistence

    Returns:
        State update with compensation and availability
    """
    avail_norm = availability.lower().strip()

    if avail_norm not in VALID_AVAILABILITY:
        return {
            "success": False,
            "error": f"Invalid availability. Choose from: {', '.join(VALID_AVAILABILITY)}",
        }

    if day_rate_min > day_rate_max:
        return {
            "success": False,
            "error": "Minimum rate cannot exceed maximum rate.",
        }

    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.update_search_prefs(user_id, day_rate_min, day_rate_max, avail_norm)
                print(f"[TOOLS] Persisted search_prefs rate={day_rate_min}-{day_rate_max}, avail={avail_norm} for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to persist search_prefs: {e}")

    return {
        "success": True,
        "day_rate_min": day_rate_min,
        "day_rate_max": day_rate_max,
        "availability": avail_norm,
        "current_step": 5,
        "next_step": "complete",
        "message": f"Rate range: {day_rate_min}-{day_rate_max}/day, available: {avail_norm}.",
    }


@tool(args_schema=CompleteOnboardingInput)
async def complete_onboarding(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark onboarding as complete and confirm profile is ready.

    Args:
        user_id: Optional user ID for persistence

    Returns:
        State update marking onboarding complete
    """
    # Persist to Neon if user_id provided - AWAIT to ensure write completes
    if user_id:
        client = _get_neon_client()
        if client:
            try:
                await client.complete_onboarding(user_id)
                print(f"[TOOLS] Marked onboarding complete for user={user_id}")
            except Exception as e:
                print(f"[TOOLS] Failed to complete onboarding: {e}")

    return {
        "success": True,
        "completed": True,
        "current_step": 6,
        "message": "Your profile is complete! I can now help you find opportunities.",
    }


# Export all tools as a list
ONBOARDING_TOOLS = [
    get_profile_status,  # Use this first to determine workflow routing
    confirm_role_preference,
    confirm_trinity,
    confirm_experience,
    confirm_location,
    confirm_search_prefs,
    complete_onboarding,
]
