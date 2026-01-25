"""
Neon PostgreSQL persistence layer using asyncpg.

Provides async database operations for user profiles.
"""

import os
from typing import Any
from contextlib import asynccontextmanager

import asyncpg


class NeonClient:
    """Async PostgreSQL client for Neon database."""

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        if not self.database_url:
            raise RuntimeError("DATABASE_URL not set")
        self._pool: asyncpg.Pool | None = None

    async def connect(self):
        """Create connection pool."""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                ssl="require",
            )
        return self._pool

    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None

    @asynccontextmanager
    async def acquire(self):
        """Acquire a connection from the pool."""
        pool = await self.connect()
        async with pool.acquire() as conn:
            yield conn

    # =========================================================================
    # User Profile Operations
    # =========================================================================

    async def get_profile(self, user_id: str) -> dict[str, Any] | None:
        """Get user profile by user_id."""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM user_profiles WHERE user_id = $1
                """,
                user_id,
            )
            return dict(row) if row else None

    async def upsert_profile(self, user_id: str, **fields) -> dict[str, Any]:
        """Create or update user profile."""
        # Build dynamic SET clause for updates
        set_parts = []
        values = [user_id]
        param_idx = 2

        for key, value in fields.items():
            if value is not None:
                set_parts.append(f"{key} = ${param_idx}")
                values.append(value)
                param_idx += 1

        if not set_parts:
            # No fields to update, just return existing or create empty
            existing = await self.get_profile(user_id)
            if existing:
                return existing

            async with self.acquire() as conn:
                row = await conn.fetchrow(
                    """
                    INSERT INTO user_profiles (user_id)
                    VALUES ($1)
                    ON CONFLICT (user_id) DO NOTHING
                    RETURNING *
                    """,
                    user_id,
                )
                return dict(row) if row else await self.get_profile(user_id)

        # Build the UPSERT query
        update_clause = ", ".join(set_parts)
        insert_columns = ["user_id"] + list(fields.keys())
        insert_placeholders = ", ".join(f"${i+1}" for i in range(len(insert_columns)))
        conflict_updates = ", ".join(f"{k} = EXCLUDED.{k}" for k in fields.keys())

        async with self.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                INSERT INTO user_profiles ({", ".join(insert_columns)})
                VALUES ({insert_placeholders})
                ON CONFLICT (user_id) DO UPDATE SET
                    {conflict_updates},
                    updated_at = NOW()
                RETURNING *
                """,
                *values,
            )
            return dict(row) if row else {}

    async def update_role_preference(self, user_id: str, role: str) -> dict[str, Any]:
        """Update user's role preference."""
        return await self.upsert_profile(user_id, role_preference=role)

    async def update_trinity(self, user_id: str, trinity: str) -> dict[str, Any]:
        """Update user's engagement type (trinity)."""
        return await self.upsert_profile(user_id, trinity=trinity)

    async def update_experience(
        self, user_id: str, years: int, industries: list[str]
    ) -> dict[str, Any]:
        """Update user's experience."""
        return await self.upsert_profile(
            user_id, experience_years=years, industries=industries
        )

    async def update_location(
        self, user_id: str, location: str, remote_preference: str
    ) -> dict[str, Any]:
        """Update user's location preferences."""
        return await self.upsert_profile(
            user_id, location=location, remote_preference=remote_preference
        )

    async def update_search_prefs(
        self, user_id: str, day_rate_min: int, day_rate_max: int, availability: str
    ) -> dict[str, Any]:
        """Update user's search preferences."""
        return await self.upsert_profile(
            user_id,
            day_rate_min=day_rate_min,
            day_rate_max=day_rate_max,
            availability=availability,
        )

    async def complete_onboarding(self, user_id: str) -> dict[str, Any]:
        """Mark user's onboarding as complete."""
        return await self.upsert_profile(user_id, onboarding_completed=True)

    # =========================================================================
    # Job Operations
    # =========================================================================

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get a job by ID."""
        async with self.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM jobs WHERE id = $1 AND is_active = true
                """,
                job_id,
            )
            if row:
                result = dict(row)
                # Convert UUID to string for JSON serialization
                result["id"] = str(result["id"])
                return result
            return None

    async def search_jobs(
        self,
        role_type: str | None = None,
        engagement_type: str | None = None,
        location: str | None = None,
        remote_preference: str | None = None,
        min_day_rate: int | None = None,
        max_day_rate: int | None = None,
        industries: list[str] | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search jobs with optional filters."""
        conditions = ["is_active = true"]
        params = []
        param_idx = 1

        if role_type:
            conditions.append(f"role_type = ${param_idx}")
            params.append(role_type.lower())
            param_idx += 1

        if engagement_type:
            conditions.append(f"engagement_type = ${param_idx}")
            params.append(engagement_type.lower())
            param_idx += 1

        if location:
            conditions.append(f"(location ILIKE ${param_idx} OR location = 'Remote')")
            params.append(f"%{location}%")
            param_idx += 1

        if remote_preference:
            conditions.append(f"remote_preference = ${param_idx}")
            params.append(remote_preference.lower())
            param_idx += 1

        if min_day_rate is not None:
            conditions.append(f"day_rate_max >= ${param_idx}")
            params.append(min_day_rate)
            param_idx += 1

        if max_day_rate is not None:
            conditions.append(f"day_rate_min <= ${param_idx}")
            params.append(max_day_rate)
            param_idx += 1

        if industries:
            # Check if any of the user's industries overlap with job industries
            conditions.append(f"industries && ${param_idx}")
            params.append(industries)
            param_idx += 1

        where_clause = " AND ".join(conditions)
        params.append(limit)

        async with self.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, title, company, role_type, engagement_type,
                       location, remote_preference, day_rate_min, day_rate_max,
                       industries, posted_at
                FROM jobs
                WHERE {where_clause}
                ORDER BY posted_at DESC
                LIMIT ${param_idx}
                """,
                *params,
            )
            return [
                {**dict(row), "id": str(row["id"])}
                for row in rows
            ]

    async def match_jobs_to_profile(
        self, user_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """Find jobs matching user's profile with match scoring."""
        # Get user profile
        profile = await self.get_profile(user_id)
        if not profile:
            return []

        # Build matching query with scoring
        async with self.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    j.*,
                    (
                        CASE WHEN j.role_type = $1 THEN 30 ELSE 0 END +
                        CASE WHEN j.engagement_type = $2 THEN 20 ELSE 0 END +
                        CASE WHEN j.location ILIKE $3 OR j.location = 'Remote' OR j.remote_preference = 'remote' THEN 15 ELSE 0 END +
                        CASE WHEN j.remote_preference = $4 THEN 10 ELSE 0 END +
                        CASE WHEN j.day_rate_min >= $5 AND j.day_rate_max <= $6 THEN 15 ELSE
                              CASE WHEN j.day_rate_max >= $5 OR j.day_rate_min <= $6 THEN 5 ELSE 0 END
                        END +
                        CASE WHEN j.industries && $7 THEN 10 ELSE 0 END
                    ) as match_score
                FROM jobs j
                WHERE j.is_active = true
                ORDER BY match_score DESC, j.posted_at DESC
                LIMIT $8
                """,
                profile.get("role_preference", ""),
                profile.get("trinity", ""),
                f"%{profile.get('location', '')}%",
                profile.get("remote_preference", ""),
                profile.get("day_rate_min", 0),
                profile.get("day_rate_max", 999999),
                profile.get("industries", []),
                limit,
            )
            return [
                {
                    **{k: v for k, v in dict(row).items() if k != "match_score"},
                    "id": str(row["id"]),
                    "match_score": row["match_score"],
                    "match_percentage": min(100, row["match_score"]),
                }
                for row in rows
            ]

    async def save_job(
        self, user_id: str, job_id: str, notes: str | None = None
    ) -> dict[str, Any] | None:
        """Save a job for a user."""
        async with self.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO saved_jobs (user_id, job_id, notes)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id, job_id) DO UPDATE SET
                        notes = COALESCE($3, saved_jobs.notes),
                        saved_at = NOW()
                    RETURNING *
                    """,
                    user_id,
                    job_id,
                    notes,
                )
                if row:
                    result = dict(row)
                    result["id"] = str(result["id"])
                    result["user_id"] = str(result["user_id"])
                    result["job_id"] = str(result["job_id"])
                    return result
                return None
            except Exception as e:
                print(f"[NEON] Error saving job: {e}")
                return None

    async def get_saved_jobs(
        self, user_id: str, status: str | None = None
    ) -> list[dict[str, Any]]:
        """Get user's saved jobs with job details."""
        conditions = ["sj.user_id = $1"]
        params = [user_id]
        param_idx = 2

        if status:
            conditions.append(f"sj.status = ${param_idx}")
            params.append(status)
            param_idx += 1

        where_clause = " AND ".join(conditions)

        async with self.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT
                    sj.id as saved_id,
                    sj.status,
                    sj.notes,
                    sj.saved_at,
                    j.id as job_id,
                    j.title,
                    j.company,
                    j.role_type,
                    j.engagement_type,
                    j.location,
                    j.remote_preference,
                    j.day_rate_min,
                    j.day_rate_max
                FROM saved_jobs sj
                JOIN jobs j ON j.id = sj.job_id
                WHERE {where_clause}
                ORDER BY sj.saved_at DESC
                """,
                *params,
            )
            return [
                {
                    **dict(row),
                    "saved_id": str(row["saved_id"]),
                    "job_id": str(row["job_id"]),
                }
                for row in rows
            ]

    async def update_saved_job_status(
        self,
        user_id: str,
        job_id: str,
        status: str,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Update status of a saved job."""
        async with self.acquire() as conn:
            if notes:
                row = await conn.fetchrow(
                    """
                    UPDATE saved_jobs
                    SET status = $3, notes = $4
                    WHERE user_id = $1 AND job_id = $2
                    RETURNING *
                    """,
                    user_id,
                    job_id,
                    status,
                    notes,
                )
            else:
                row = await conn.fetchrow(
                    """
                    UPDATE saved_jobs
                    SET status = $3
                    WHERE user_id = $1 AND job_id = $2
                    RETURNING *
                    """,
                    user_id,
                    job_id,
                    status,
                )
            if row:
                result = dict(row)
                result["id"] = str(result["id"])
                result["user_id"] = str(result["user_id"])
                result["job_id"] = str(result["job_id"])
                return result
            return None


# Global client instance
_client: NeonClient | None = None


def get_neon_client() -> NeonClient:
    """Get or create the global Neon client."""
    global _client
    if _client is None:
        _client = NeonClient()
    return _client
