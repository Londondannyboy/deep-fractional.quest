import { NextRequest, NextResponse } from 'next/server';

// CLM endpoint for Hume EVI - proxies to DeepAgents
// This makes voice use the SAME brain as the CopilotKit chat

const AGENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL || 'http://localhost:8123';
const ZEP_API_KEY = process.env.ZEP_API_KEY || '';

interface OpenAIMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AGUIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'developer';
  content: string;
}

// Fetch Zep context for the user
async function getZepContext(userId: string): Promise<string> {
  if (!userId || !ZEP_API_KEY) return '';

  try {
    const response = await fetch('https://api.getzep.com/api/v2/graph/search', {
      method: 'POST',
      headers: {
        'Authorization': `Api-Key ${ZEP_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        query: 'user preferences interests roles locations experience',
        limit: 10,
        scope: 'edges',
      }),
    });

    if (!response.ok) return '';

    const data = await response.json();
    const edges = data.edges || [];
    const facts = edges.slice(0, 5).map((e: { fact?: string }) => `- ${e.fact}`).filter(Boolean);

    if (facts.length > 0) {
      return `\n\nWhat I remember about you:\n${facts.join('\n')}`;
    }
    return '';
  } catch {
    return '';
  }
}

// Parse SSE stream and extract text content
async function parseSSEStream(response: Response): Promise<string> {
  const reader = response.body?.getReader();
  if (!reader) return '';

  const decoder = new TextDecoder();
  let content = '';
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            // Extract text content from various event types
            if (data.type === 'TEXT_MESSAGE_CONTENT' || data.type === 'TextMessageContent') {
              content += data.content || data.delta || '';
            }
            // Handle Deep Agents streaming format
            else if (data.delta?.content) {
              content += data.delta.content;
            }
            // Handle direct content
            else if (data.content && typeof data.content === 'string') {
              content += data.content;
            }
          } catch {
            // Skip non-JSON data lines
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return content.trim();
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const messages: OpenAIMessage[] = body.messages || [];

    // Extract metadata from Hume (custom session ID format: "firstName|deep_fractional_userId|pageContext")
    const customSessionId = body.custom_session_id || body.session_id || '';
    const sessionParts = customSessionId.split('|');
    const firstName = sessionParts[0] || '';
    const sessionPart = sessionParts[1] || '';
    const rawUserId = sessionPart?.replace('deep_fractional_', '') || '';

    // Only treat as authenticated if userId is NOT anonymous (anonymous IDs start with 'anon_')
    const isAuthenticated = rawUserId && !rawUserId.startsWith('anon_');
    const userId = isAuthenticated ? rawUserId : '';

    // Parse page context if included (format: "location:London,jobs:25")
    const pageContextStr = sessionParts[2] || '';
    let pageContext: { location?: string; totalJobs?: number } | null = null;
    if (pageContextStr) {
      const parts = pageContextStr.split(',');
      pageContext = {};
      parts.forEach((p: string) => {
        const [key, val] = p.split(':');
        if (key === 'location') pageContext!.location = val;
        if (key === 'jobs') pageContext!.totalJobs = parseInt(val, 10);
      });
    }

    // Get the conversation history
    const userMessages = messages.filter(m => m.role === 'user');
    const lastUserMessage = userMessages[userMessages.length - 1]?.content || '';

    console.log('[CLM] Received from Hume:', lastUserMessage.slice(0, 100));
    console.log('[CLM] User:', firstName || 'guest', 'Authenticated:', isAuthenticated, 'UserId:', userId || 'none');

    // Fetch Zep context if we have a user ID
    const zepContext = userId ? await getZepContext(userId) : '';

    // Build AG-UI compatible message array
    const aguiMessages: AGUIMessage[] = [];

    // Build page context string
    let pageContextString = '';
    if (pageContext?.location) {
      pageContextString = `
PAGE CONTEXT - CRITICAL:
User is currently viewing: ${pageContext.location.toUpperCase()} context
${pageContext.totalJobs ? `- Total relevant items: ${pageContext.totalJobs}` : ''}
`;
    }

    // Add system context as a developer message
    const systemContext = `You are a helpful career advisor for a fractional executive platform.
${firstName ? `The user's name is ${firstName}.` : ''}
${zepContext}
${pageContextString}

IMPORTANT: Keep responses concise for voice - 1-2 sentences unless more detail is requested.
Help users with onboarding, finding jobs, and booking coaching sessions.
When users ask about jobs, USE THE search_jobs TOOL to find real jobs from the database!`;

    aguiMessages.push({
      id: `sys_${Date.now()}`,
      role: 'developer',
      content: systemContext,
    });

    // Convert OpenAI messages to AG-UI format
    messages.forEach((msg, idx) => {
      aguiMessages.push({
        id: `msg_${idx}_${Date.now()}`,
        role: msg.role === 'system' ? 'developer' : msg.role,
        content: msg.content,
      });
    });

    // Build the AG-UI request body
    // IMPORTANT: user_id at top-level is required by agent tools for database persistence
    const agentRequestBody = {
      messages: aguiMessages,
      runId: `run_${Date.now()}`,
      threadId: sessionPart || `thread_${Date.now()}`,
      state: {
        // user_id at top level for tool persistence (matches useCopilotReadable in chat UI)
        user_id: userId || null,
        user_name: firstName || null,
        jobs: [],
        search_query: '',
        user: userId ? { id: userId, name: firstName } : null,
        page_context: pageContext ? {
          page_type: `context_${pageContext.location?.toLowerCase() || 'main'}`,
          location_filter: pageContext.location || null,
          total_jobs: pageContext.totalJobs || null,
        } : null,
      },
    };

    console.log('[CLM] Calling DeepAgents at:', AGENT_URL);
    console.log('[CLM] State user_id:', agentRequestBody.state.user_id || 'none (anonymous)');

    // Call the DeepAgents agent
    const agentResponse = await fetch(AGENT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(agentRequestBody),
    });

    if (!agentResponse.ok) {
      console.error('[CLM] Agent error:', agentResponse.status, agentResponse.statusText);
      throw new Error(`Agent returned ${agentResponse.status}`);
    }

    // Parse the SSE stream and extract text content
    const responseText = await parseSSEStream(agentResponse);

    console.log('[CLM] Agent response:', responseText.slice(0, 100));

    // Store conversation to Zep in real-time (backup to webhook)
    // Only store for authenticated users (userId is empty for anonymous)
    if (userId && ZEP_API_KEY) {
      console.log('[CLM] Storing to Zep for authenticated user:', userId);
      try {
        // Store user message
        await fetch('https://api.getzep.com/api/v2/sessions', {
          method: 'POST',
          headers: {
            'Authorization': `Api-Key ${ZEP_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            session_id: `voice_${sessionPart}`,
            user_id: userId,
            metadata: { source: 'hume_clm', page: pageContext?.location || 'main' },
          }),
        });

        // Store the exchange
        await fetch(`https://api.getzep.com/api/v2/sessions/voice_${sessionPart}/messages`, {
          method: 'POST',
          headers: {
            'Authorization': `Api-Key ${ZEP_API_KEY}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify([
            { role_type: 'user', content: lastUserMessage },
            { role_type: 'assistant', content: responseText },
          ]),
        });
        console.log('[CLM] Stored exchange to Zep');
      } catch (e) {
        console.warn('[CLM] Failed to store to Zep:', e);
      }
    } else if (!userId) {
      console.log('[CLM] Skipping Zep storage for anonymous user');
    }

    // Return OpenAI-compatible response for Hume
    return NextResponse.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: 'deep-agents',
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: responseText || "I'm here to help you find fractional executive opportunities. What type of position interests you?",
        },
        finish_reason: 'stop',
      }],
      usage: {
        prompt_tokens: lastUserMessage.length,
        completion_tokens: responseText.length,
        total_tokens: lastUserMessage.length + responseText.length,
      },
    });

  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : 'Unknown error';
    console.error('[CLM] Error:', message);

    // Fallback response
    return NextResponse.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: 'deep-agents-fallback',
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: "I'm having trouble connecting right now. Could you try again in a moment?",
        },
        finish_reason: 'stop',
      }],
    });
  }
}
