import { NextRequest, NextResponse } from 'next/server';

// CLM endpoint for Hume EVI - proxies to DeepAgents
// Implements Christian Bromann's voice + LangGraph interrupt pattern
// https://github.com/christian-bromann/createVoiceAgent

const AGENT_URL = process.env.LANGGRAPH_DEPLOYMENT_URL;
if (!AGENT_URL) {
  console.error('[CLM] FATAL: LANGGRAPH_DEPLOYMENT_URL not set');
}
const ZEP_API_KEY = process.env.ZEP_API_KEY || '';

// Track pending interrupts per thread (Christian's pattern)
// In production, use Redis or database
const pendingInterrupts = new Map<string, {
  toolName: string;
  toolCallId: string;
  args: Record<string, unknown>;
  prompt: string;
}>();

interface OpenAIMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface AGUIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'developer';
  content: string;
}

interface ParsedResponse {
  content: string;
  interrupt?: {
    toolName: string;
    toolCallId: string;
    args: Record<string, unknown>;
  };
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

// Parse SSE stream and extract text content + detect interrupts
async function parseSSEStream(response: Response): Promise<ParsedResponse> {
  const reader = response.body?.getReader();
  if (!reader) return { content: '' };

  const decoder = new TextDecoder();
  let content = '';
  let buffer = '';
  let interrupt: ParsedResponse['interrupt'] | undefined;

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

            // Detect interrupt events (HITL tools)
            if (data.type === 'TOOL_CALL_START' || data.type === 'ToolCallStart') {
              // Check if this is an HITL tool
              const hitlTools = [
                'confirm_role_preference', 'confirm_trinity', 'confirm_experience',
                'confirm_location', 'confirm_search_prefs', 'complete_onboarding',
                'save_job', 'update_job_status', 'schedule_session', 'cancel_session'
              ];
              if (hitlTools.includes(data.name || data.tool_name)) {
                interrupt = {
                  toolName: data.name || data.tool_name,
                  toolCallId: data.id || data.tool_call_id || `call_${Date.now()}`,
                  args: data.args || data.arguments || {},
                };
                console.log('[CLM] Detected HITL interrupt:', interrupt.toolName);
              }
            }

            // Also check for interrupt state in the response
            if (data.type === 'INTERRUPT' || data.interrupt) {
              console.log('[CLM] Received interrupt event:', data);
              if (!interrupt && data.tool_name) {
                interrupt = {
                  toolName: data.tool_name,
                  toolCallId: data.tool_call_id || `call_${Date.now()}`,
                  args: data.args || {},
                };
              }
            }

            // Extract text content from various event types
            if (data.type === 'TEXT_MESSAGE_CONTENT' || data.type === 'TextMessageContent') {
              content += data.content || data.delta || '';
            }
            // Handle Deep Agents streaming format
            else if (data.delta?.content) {
              content += data.delta.content;
            }
            // Handle direct content
            else if (data.content && typeof data.content === 'string' && !data.type?.includes('TOOL')) {
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

  return { content: content.trim(), interrupt };
}

// Generate voice-friendly confirmation prompt
function getConfirmationPrompt(toolName: string, args: Record<string, unknown>): string {
  switch (toolName) {
    case 'confirm_role_preference':
      return `I'd like to save ${String(args.role || 'this role').toUpperCase()} as your target role. Say "yes" to confirm, or "no" to cancel.`;
    case 'confirm_trinity':
      return `Should I save ${args.trinity || 'this'} as your engagement preference? Say "yes" or "no".`;
    case 'confirm_experience':
      return `I'll save ${args.years || 'your'} years of experience. Confirm with "yes" or "no".`;
    case 'confirm_location':
      return `Save ${args.location || 'this location'} with ${args.remote_preference || 'flexible'} remote preference? Say "yes" or "no".`;
    case 'confirm_search_prefs':
      return `I'll set your day rate to ${args.day_rate_min}-${args.day_rate_max} with ${args.availability || 'flexible'} availability. Confirm?`;
    case 'complete_onboarding':
      return `Ready to complete your profile setup? Say "yes" to finish onboarding.`;
    case 'save_job':
      return `Would you like me to save this job to your list? Say "yes" or "no".`;
    default:
      return `Should I proceed with this action? Say "yes" to confirm.`;
  }
}

// Check if user message is a confirmation
function isConfirmation(message: string): boolean {
  const msg = message.toLowerCase().trim();
  return ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay', 'confirm', 'do it', 'go ahead', 'please'].some(
    word => msg.includes(word)
  );
}

function isDenial(message: string): boolean {
  const msg = message.toLowerCase().trim();
  return ['no', 'nope', 'cancel', 'stop', 'don\'t', 'dont', 'never mind'].some(
    word => msg.includes(word)
  );
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
    const threadId = sessionPart || `thread_${Date.now()}`;

    // Only treat as authenticated if userId is NOT anonymous
    const isAuthenticated = rawUserId && !rawUserId.startsWith('anon_');
    const userId = isAuthenticated ? rawUserId : '';

    // Parse page context if included
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
    console.log('[CLM] User:', firstName || 'guest', 'UserId:', userId || 'none', 'ThreadId:', threadId);

    // ============================================
    // CHRISTIAN'S PATTERN: Check for pending interrupt
    // ============================================
    const pendingInterrupt = pendingInterrupts.get(threadId);

    if (pendingInterrupt) {
      console.log('[CLM] Found pending interrupt for thread:', threadId, pendingInterrupt.toolName);

      // Check if user confirmed or denied
      if (isConfirmation(lastUserMessage)) {
        console.log('[CLM] User confirmed interrupt - resuming with confirmed: true');
        pendingInterrupts.delete(threadId);

        // Call agent with resume command
        // The agent should complete the tool with confirmed: true
        const resumeBody = {
          messages: [{
            id: `resume_${Date.now()}`,
            role: 'user',
            content: `User confirmed: "${lastUserMessage}". Complete the ${pendingInterrupt.toolName} tool with confirmed: true.`,
          }],
          runId: `run_${Date.now()}`,
          threadId: threadId,
          state: {
            user_id: userId || null,
            // Signal to resume the interrupt
            resume_interrupt: {
              tool_call_id: pendingInterrupt.toolCallId,
              confirmed: true,
            },
          },
        };

        const agentResponse = await fetch(AGENT_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Accept': 'text/event-stream' },
          body: JSON.stringify(resumeBody),
        });

        if (agentResponse.ok) {
          const { content } = await parseSSEStream(agentResponse);
          return NextResponse.json({
            id: `chatcmpl-${Date.now()}`,
            object: 'chat.completion',
            created: Math.floor(Date.now() / 1000),
            model: 'deep-agents',
            choices: [{
              index: 0,
              message: {
                role: 'assistant',
                content: content || `Great! I've saved your ${pendingInterrupt.toolName.replace('confirm_', '').replace('_', ' ')} preference.`,
              },
              finish_reason: 'stop',
            }],
          });
        }
      } else if (isDenial(lastUserMessage)) {
        console.log('[CLM] User denied interrupt - cancelling');
        pendingInterrupts.delete(threadId);

        return NextResponse.json({
          id: `chatcmpl-${Date.now()}`,
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: 'deep-agents',
          choices: [{
            index: 0,
            message: {
              role: 'assistant',
              content: `No problem, I won't save that. What else can I help you with?`,
            },
            finish_reason: 'stop',
          }],
        });
      } else {
        // User said something else - repeat the prompt
        console.log('[CLM] User response unclear - repeating prompt');
        return NextResponse.json({
          id: `chatcmpl-${Date.now()}`,
          object: 'chat.completion',
          created: Math.floor(Date.now() / 1000),
          model: 'deep-agents',
          choices: [{
            index: 0,
            message: {
              role: 'assistant',
              content: `I didn't catch that. ${pendingInterrupt.prompt}`,
            },
            finish_reason: 'stop',
          }],
        });
      }
    }

    // ============================================
    // No pending interrupt - normal agent call
    // ============================================

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
${userId ? `CRITICAL - USER ID FOR TOOLS: ${userId}
When calling ANY tool that accepts user_id, you MUST pass this user_id: "${userId}"
This enables saving data to the user's profile in the database.` : 'User is not logged in - data will not persist.'}
${zepContext}
${pageContextString}

IMPORTANT: Keep responses concise for voice - 1-2 sentences unless more detail is requested.
Help users with onboarding, finding jobs, and booking coaching sessions.
When users ask about jobs, USE THE search_jobs or hybrid_search_jobs TOOL to find real jobs!`;

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
    const agentRequestBody = {
      messages: aguiMessages,
      runId: `run_${Date.now()}`,
      threadId: threadId,
      state: {
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

    // Parse the SSE stream and extract text content + detect interrupts
    const { content: responseText, interrupt } = await parseSSEStream(agentResponse);

    console.log('[CLM] Agent response:', responseText.slice(0, 100));

    // ============================================
    // CHRISTIAN'S PATTERN: Handle new interrupt
    // ============================================
    if (interrupt) {
      console.log('[CLM] Storing interrupt for voice confirmation:', interrupt.toolName);

      const prompt = getConfirmationPrompt(interrupt.toolName, interrupt.args);

      pendingInterrupts.set(threadId, {
        toolName: interrupt.toolName,
        toolCallId: interrupt.toolCallId,
        args: interrupt.args,
        prompt: prompt,
      });

      // Return the confirmation prompt for voice
      return NextResponse.json({
        id: `chatcmpl-${Date.now()}`,
        object: 'chat.completion',
        created: Math.floor(Date.now() / 1000),
        model: 'deep-agents',
        choices: [{
          index: 0,
          message: {
            role: 'assistant',
            content: responseText ? `${responseText} ${prompt}` : prompt,
          },
          finish_reason: 'stop',
        }],
      });
    }

    // Store conversation to Zep
    if (userId && ZEP_API_KEY) {
      try {
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
      } catch (e) {
        console.warn('[CLM] Failed to store to Zep:', e);
      }
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
