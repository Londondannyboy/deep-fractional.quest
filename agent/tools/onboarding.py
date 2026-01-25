"""
Onboarding tools for Fractional Quest.

Each tool confirms a piece of user profile information
and returns state updates that sync to the frontend.
"""

from langchain.tools import tool
from typing import Dict, Any, List
import json


# Valid values for validation
VALID_ROLES = ["cto", "cfo", "cmo", "coo", "cpo", "other"]
VALID_TRINITY = ["fractional", "interim", "advisory", "open"]
VALID_REMOTE = ["remote", "hybrid", "onsite", "flexible"]
VALID_AVAILABILITY = ["immediately", "1_month", "3_months", "flexible"]


@tool
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


@tool
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


@tool
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


@tool
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
