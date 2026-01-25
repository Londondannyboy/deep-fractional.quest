"""
Onboarding tools for Fractional Quest.

Each tool confirms a piece of user profile information
and returns state updates that sync to the frontend.

Uses Pydantic schemas for input validation (args_schema).
Optionally persists to Neon PostgreSQL when user_id is provided.
"""

import asyncio
from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Literal, Optional
import json

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


def _persist_async(coro):
    """Run async persistence in background, don't block tool execution."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(coro)
        else:
            loop.run_until_complete(coro)
    except Exception as e:
        print(f"[TOOLS] Persistence error: {e}")


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
# Tools with Pydantic Schemas
# =============================================================================

@tool(args_schema=RolePreferenceInput)
def confirm_role_preference(role: str, user_id: Optional[str] = None) -> Dict[str, Any]:
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

    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.update_role_preference(user_id, normalized))

    return {
        "success": True,
        "role_preference": normalized,
        "current_step": 1,
        "next_step": "trinity",
        "message": f"Great! I've noted your preference for {normalized.upper()} roles.",
    }


@tool(args_schema=TrinityInput)
def confirm_trinity(engagement_type: str, user_id: Optional[str] = None) -> Dict[str, Any]:
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

    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.update_trinity(user_id, normalized))

    return {
        "success": True,
        "trinity": normalized,
        "current_step": 2,
        "next_step": "experience",
        "message": f"Perfect! You're looking for {normalized} opportunities.",
    }


@tool(args_schema=ExperienceInput)
def confirm_experience(years: int, industries: str, user_id: Optional[str] = None) -> Dict[str, Any]:
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

    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.update_experience(user_id, years, industry_list))

    return {
        "success": True,
        "experience_years": years,
        "industries": industry_list,
        "current_step": 3,
        "next_step": "location",
        "message": f"Got it! {years} years across {', '.join(industry_list)}.",
    }


@tool(args_schema=LocationInput)
def confirm_location(location: str, remote_preference: str, user_id: Optional[str] = None) -> Dict[str, Any]:
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

    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.update_location(user_id, location.strip(), remote_norm))

    return {
        "success": True,
        "location": location.strip(),
        "remote_preference": remote_norm,
        "current_step": 4,
        "next_step": "search_prefs",
        "message": f"Location: {location}, preference: {remote_norm}.",
    }


@tool(args_schema=SearchPrefsInput)
def confirm_search_prefs(
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

    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.update_search_prefs(user_id, day_rate_min, day_rate_max, avail_norm))

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
def complete_onboarding(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark onboarding as complete and confirm profile is ready.

    Args:
        user_id: Optional user ID for persistence

    Returns:
        State update marking onboarding complete
    """
    # Persist to Neon if user_id provided
    if user_id:
        client = _get_neon_client()
        if client:
            _persist_async(client.complete_onboarding(user_id))

    return {
        "success": True,
        "completed": True,
        "current_step": 6,
        "message": "Your profile is complete! I can now help you find opportunities.",
    }


# Export all tools as a list
ONBOARDING_TOOLS = [
    confirm_role_preference,
    confirm_trinity,
    confirm_experience,
    confirm_location,
    confirm_search_prefs,
    complete_onboarding,
]
