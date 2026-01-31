import { NextRequest, NextResponse } from 'next/server';
import { neon } from '@neondatabase/serverless';

// Get Neon SQL client
function getSql() {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('DATABASE_URL not set');
  }
  return neon(databaseUrl);
}

// GET /api/profile?userId=xxx - Fetch user profile
export async function GET(req: NextRequest) {
  try {
    const userId = req.nextUrl.searchParams.get('userId');

    if (!userId) {
      return NextResponse.json({ error: 'userId required' }, { status: 400 });
    }

    const sql = getSql();
    const rows = await sql`
      SELECT * FROM user_profiles WHERE user_id = ${userId}
    `;

    if (rows.length === 0) {
      // Return empty profile structure
      return NextResponse.json({
        profile: null,
        message: 'No profile found - start onboarding to create one',
      });
    }

    return NextResponse.json({
      profile: rows[0],
      message: 'Profile found',
    });
  } catch (error) {
    console.error('[PROFILE API] Error fetching profile:', error);
    return NextResponse.json(
      { error: 'Failed to fetch profile', details: String(error) },
      { status: 500 }
    );
  }
}

// POST /api/profile - Create or update profile
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { user_id, ...profileData } = body;

    if (!user_id) {
      return NextResponse.json({ error: 'user_id required' }, { status: 400 });
    }

    const sql = getSql();

    // Build the upsert query dynamically based on provided fields
    const validFields = [
      'role_preference',
      'trinity',
      'experience_years',
      'industries',
      'location',
      'remote_preference',
      'day_rate_min',
      'day_rate_max',
      'availability',
      'onboarding_completed',
    ];

    // Filter to only valid fields
    const updates: Record<string, any> = {};
    for (const field of validFields) {
      if (profileData[field] !== undefined) {
        updates[field] = profileData[field];
      }
    }

    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ error: 'No valid fields to update' }, { status: 400 });
    }

    // Check if profile exists
    const existing = await sql`
      SELECT id FROM user_profiles WHERE user_id = ${user_id}
    `;

    let result;
    if (existing.length === 0) {
      // Insert new profile
      result = await sql`
        INSERT INTO user_profiles (
          id, user_id,
          role_preference, trinity, experience_years, industries,
          location, remote_preference, day_rate_min, day_rate_max,
          availability, onboarding_completed, created_at, updated_at
        ) VALUES (
          gen_random_uuid(), ${user_id},
          ${updates.role_preference || null},
          ${updates.trinity || null},
          ${updates.experience_years || null},
          ${updates.industries || null},
          ${updates.location || null},
          ${updates.remote_preference || null},
          ${updates.day_rate_min || null},
          ${updates.day_rate_max || null},
          ${updates.availability || null},
          ${updates.onboarding_completed || false},
          NOW(), NOW()
        )
        RETURNING *
      `;
    } else {
      // Update existing profile
      result = await sql`
        UPDATE user_profiles
        SET
          role_preference = COALESCE(${updates.role_preference}, role_preference),
          trinity = COALESCE(${updates.trinity}, trinity),
          experience_years = COALESCE(${updates.experience_years}, experience_years),
          industries = COALESCE(${updates.industries}, industries),
          location = COALESCE(${updates.location}, location),
          remote_preference = COALESCE(${updates.remote_preference}, remote_preference),
          day_rate_min = COALESCE(${updates.day_rate_min}, day_rate_min),
          day_rate_max = COALESCE(${updates.day_rate_max}, day_rate_max),
          availability = COALESCE(${updates.availability}, availability),
          onboarding_completed = COALESCE(${updates.onboarding_completed}, onboarding_completed),
          updated_at = NOW()
        WHERE user_id = ${user_id}
        RETURNING *
      `;
    }

    return NextResponse.json({
      success: true,
      profile: result[0],
      message: existing.length === 0 ? 'Profile created' : 'Profile updated',
    });
  } catch (error) {
    console.error('[PROFILE API] Error updating profile:', error);
    return NextResponse.json(
      { error: 'Failed to update profile', details: String(error) },
      { status: 500 }
    );
  }
}
