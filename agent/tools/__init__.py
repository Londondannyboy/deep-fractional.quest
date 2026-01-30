"""Tools for Fractional Quest agent."""

from .onboarding import (
    get_profile_status,
    confirm_role_preference,
    confirm_trinity,
    confirm_experience,
    confirm_location,
    confirm_search_prefs,
    complete_onboarding,
    ONBOARDING_TOOLS,
)

from .jobs import (
    search_jobs,
    hybrid_search_jobs,
    match_jobs,
    save_job,
    get_saved_jobs,
    update_job_status,
    get_job_details,
    JOB_TOOLS,
)

from .memory import (
    get_user_memory,
    save_user_preference,
    save_user_fact,
    MEMORY_TOOLS,
)

__all__ = [
    # Onboarding tools
    "get_profile_status",
    "confirm_role_preference",
    "confirm_trinity",
    "confirm_experience",
    "confirm_location",
    "confirm_search_prefs",
    "complete_onboarding",
    "ONBOARDING_TOOLS",
    # Job tools
    "search_jobs",
    "hybrid_search_jobs",
    "match_jobs",
    "save_job",
    "get_saved_jobs",
    "update_job_status",
    "get_job_details",
    "JOB_TOOLS",
    # Memory tools
    "get_user_memory",
    "save_user_preference",
    "save_user_fact",
    "MEMORY_TOOLS",
]
