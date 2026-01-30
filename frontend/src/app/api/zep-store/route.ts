import { NextRequest, NextResponse } from 'next/server';

const ZEP_API_KEY = process.env.ZEP_API_KEY || '';

export async function POST(request: NextRequest) {
  try {
    const { userId, sessionId, role, content, metadata } = await request.json();

    if (!userId || !content || !ZEP_API_KEY) {
      return NextResponse.json({ success: false, error: 'Missing required fields' });
    }

    // Use a stable thread ID based on user ID
    const threadId = sessionId || `deep_fractional_${userId}`;

    // 1. Ensure user exists in Zep
    await fetch('https://api.getzep.com/api/v2/users', {
      method: 'POST',
      headers: {
        'Authorization': `Api-Key ${ZEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ user_id: userId }),
    });

    // 2. Create/get thread
    await fetch('https://api.getzep.com/api/v2/threads', {
      method: 'POST',
      headers: {
        'Authorization': `Api-Key ${ZEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        thread_id: threadId,
        user_id: userId,
        metadata: { source: 'deep-fractional-copilotkit', ...metadata },
      }),
    });

    // 3. Add message to thread (Zep auto-extracts facts)
    const msgResponse = await fetch(`https://api.getzep.com/api/v2/threads/${threadId}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Api-Key ${ZEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: [{
          role: role || 'user',
          content: content,
          metadata: { source: 'voice', ...metadata },
        }],
      }),
    });

    if (!msgResponse.ok) {
      console.error('[Zep] Failed to store message:', msgResponse.status);
      return NextResponse.json({ success: false, error: 'Failed to store' });
    }

    console.log(`[Zep] Stored ${role} message for user ${userId}: ${content.slice(0, 50)}...`);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('[Zep] Error storing message:', error);
    return NextResponse.json({ success: false, error: 'Server error' });
  }
}
