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


# Global client instance
_client: NeonClient | None = None


def get_neon_client() -> NeonClient:
    """Get or create the global Neon client."""
    global _client
    if _client is None:
        _client = NeonClient()
    return _client
