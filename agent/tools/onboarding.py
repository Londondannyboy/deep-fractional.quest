"""
Onboarding tools for Fractional Quest.

Each tool confirms a piece of user profile information
and returns state updates that sync to the frontend.

Uses Pydantic schemas for input validation (args_schema).
"""

from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Literal
import json


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

    @field_validator("role")
    @classmethod
    def normalize_role(cls, v: str) -> str:
        return v.lower().strip()


class TrinityInput(BaseModel):
    """Input schema for confirm_trinity tool."""
    engagement_type: str = Field(
        description="Engagement type: fractional, interim, advisory, or open"
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


class LocationInput(BaseModel):
    """Input schema for confirm_location tool."""
    location: str = Field(
        description="City/country (e.g., 'London', 'New York', 'Remote')"
    )
    remote_preference: str = Field(
        description="Remote work preference: remote, hybrid, onsite, or flexible"
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

    @field_validator("availability")
    @classmethod
    def normalize_availability(cls, v: str) -> str:
        return v.lower().strip()


# =============================================================================
# Tools with Pydantic Schemas
# =============================================================================

@tool(args_schema=RolePreferenceInput)
def confirm_role_preference(role: str) -> Dict[str, Any]:
    """
    Confirm the C-level role preference.

    Args:
        role: The role type (cto, cfo, cmo, coo, cpo, or other)

    Returns:
        State update with role_preference and next step
    """
    normalized = role.lower().strip()

    if normalized not in VALID_ROLES:
        return {
            "success": False,
            "error": f"Invalid role. Please choose from: {', '.join(VALID_ROLES)}",
        }

    return {
        "success": True,
        "role_preference": normalized,
        "current_step": 1,
        "next_step": "trinity",
        "message": f"Great! I've noted your preference for {normalized.upper()} roles.",
    }


@tool(args_schema=TrinityInput)
def confirm_trinity(engagement_type: str) -> Dict[str, Any]:
    """
    Confirm the engagement type preference (fractional/interim/advisory).

    Args:
        engagement_type: One of fractional, interim, advisory, or open

    Returns:
        State update with trinity and next step
    """
    normalized = engagement_type.lower().strip()

    if normalized not in VALID_TRINITY:
        return {
            "success": False,
            "error": f"Invalid type. Please choose from: {', '.join(VALID_TRINITY)}",
        }

    return {
        "success": True,
        "trinity": normalized,
        "current_step": 2,
        "next_step": "experience",
        "message": f"Perfect! You're looking for {normalized} opportunities.",
    }


@tool(args_schema=ExperienceInput)
def confirm_experience(years: int, industries: str) -> Dict[str, Any]:
    """
    Confirm experience level and industries.

    Args:
        years: Years of executive experience
        industries: Comma-separated list of industries

    Returns:
        State update with experience and industries
    """
    if years < 0:
        return {
            "success": False,
            "error": "Years of experience must be positive.",
        }

    industry_list = [i.strip() for i in industries.split(",") if i.strip()]

    return {
        "success": True,
        "experience_years": years,
        "industries": industry_list,
        "current_step": 3,
        "next_step": "location",
        "message": f"Got it! {years} years across {', '.join(industry_list)}.",
    }


@tool(args_schema=LocationInput)
def confirm_location(location: str, remote_preference: str) -> Dict[str, Any]:
    """
    Confirm location and remote work preference.

    Args:
        location: City/country or "Remote"
        remote_preference: One of remote, hybrid, onsite, flexible

    Returns:
        State update with location info
    """
    remote_norm = remote_preference.lower().strip()

    if remote_norm not in VALID_REMOTE:
        return {
            "success": False,
            "error": f"Invalid preference. Choose from: {', '.join(VALID_REMOTE)}",
        }

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
    availability: str
) -> Dict[str, Any]:
    """
    Confirm compensation and availability.

    Args:
        day_rate_min: Minimum day rate in GBP
        day_rate_max: Maximum day rate in GBP
        availability: One of immediately, 1_month, 3_months, flexible

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

    return {
        "success": True,
        "day_rate_min": day_rate_min,
        "day_rate_max": day_rate_max,
        "availability": avail_norm,
        "current_step": 5,
        "next_step": "complete",
        "message": f"Rate range: {day_rate_min}-{day_rate_max}/day, available: {avail_norm}.",
    }


@tool
def complete_onboarding() -> Dict[str, Any]:
    """
    Mark onboarding as complete and confirm profile is ready.

    Returns:
        State update marking onboarding complete
    """
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
