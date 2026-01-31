"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { VoiceProvider, useVoice } from "@humeai/voice-react";

// Session storage keys for persistence across remounts
const SESSION_GREETED_KEY = 'hume_greeted_session';
const SESSION_LAST_INTERACTION_KEY = 'hume_last_interaction';

// Helper to get/set session storage safely (SSR-safe)
function getSessionValue(key: string, defaultValue: number | boolean): number | boolean {
  if (typeof window === 'undefined') return defaultValue;
  const stored = sessionStorage.getItem(key);
  if (stored === null) return defaultValue;
  return key.includes('time') || key.includes('interaction') ? parseInt(stored, 10) : stored === 'true';
}

function setSessionValue(key: string, value: number | boolean): void {
  if (typeof window === 'undefined') return;
  sessionStorage.setItem(key, String(value));
}

interface PageContext {
  location?: string;
  totalJobs?: number;
  pageType?: 'jobs' | 'services' | 'coaching' | 'home';
  roleType?: string;
}

interface VoiceInputProps {
  onMessage?: (text: string, role: "user" | "assistant") => void;
  firstName?: string | null;
  userId?: string | null;
  pageContext?: PageContext;
}

interface VoiceButtonProps {
  onMessage?: (text: string, role: "user" | "assistant") => void;
  firstName?: string | null;
  userId?: string | null;
  pageContext?: PageContext;
}

/**
 * Voice button component that handles Hume connection.
 */
function VoiceButton({ onMessage, firstName, userId, pageContext }: VoiceButtonProps) {
  const { connect, disconnect, status, messages, sendUserInput } = useVoice();
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastSentMsgId = useRef<string | null>(null);

  // Use sessionStorage-backed refs for persistence across remounts
  const greetedThisSession = useRef(getSessionValue(SESSION_GREETED_KEY, false) as boolean);
  const lastInteractionTime = useRef(getSessionValue(SESSION_LAST_INTERACTION_KEY, 0) as number);

  // Debug logging
  useEffect(() => {
    console.log("[VOICE] Status:", status.value);
  }, [status]);

  // Forward BOTH user AND assistant messages to CopilotKit for full context
  useEffect(() => {
    // Get all conversation messages (user + assistant)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const conversationMsgs = messages.filter(
      (m: any) => (m.type === "user_message" || m.type === "assistant_message") && m.message?.content
    );

    if (conversationMsgs.length > 0) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const lastMsg = conversationMsgs[conversationMsgs.length - 1] as any;
      const msgId = lastMsg?.id || `${conversationMsgs.length}-${lastMsg?.message?.content?.slice(0, 20)}`;

      // Only send if this is a new message we haven't sent before
      if (lastMsg?.message?.content && msgId !== lastSentMsgId.current) {
        const isUser = lastMsg.type === "user_message";
        console.log(`[VOICE] Forwarding ${isUser ? 'user' : 'assistant'} to CopilotKit:`, lastMsg.message.content.slice(0, 50));
        lastSentMsgId.current = msgId;

        // Update interaction time
        const now = Date.now();
        lastInteractionTime.current = now;
        setSessionValue(SESSION_LAST_INTERACTION_KEY, now);

        // Forward FULL content to CopilotKit with role indicator
        if (onMessage) {
          onMessage(lastMsg.message.content, isUser ? "user" : "assistant");
        }
      }
    }
  }, [messages, onMessage]);

  // Connect to Hume
  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      console.log("[VOICE] Fetching Hume token...");
      const response = await fetch("/api/hume-token");
      if (!response.ok) {
        throw new Error("Failed to get access token");
      }
      const { accessToken } = await response.json();

      // Fetch Zep context if user is logged in
      let zepContext = "";
      if (userId) {
        try {
          const zepRes = await fetch(`/api/zep-context?userId=${userId}`);
          const zepData = await zepRes.json();
          if (zepData.context) {
            zepContext = zepData.context;
            console.log("[VOICE] Zep context loaded:", zepData.facts?.length || 0, "facts");
          }
        } catch (e) {
          console.warn("[VOICE] Failed to fetch Zep context:", e);
        }
      }

      // Detect if this is a quick reconnect (< 5 mins)
      const timeSinceLastInteraction = lastInteractionTime.current > 0
        ? Date.now() - lastInteractionTime.current
        : Infinity;
      const isQuickReconnect = timeSinceLastInteraction < 5 * 60 * 1000; // 5 minutes
      const wasGreeted = greetedThisSession.current;

      // Build system prompt with anti-re-greeting logic
      let greetingInstruction = "";
      if (wasGreeted || isQuickReconnect) {
        greetingInstruction = `DO NOT GREET - already greeted this session.
- DO NOT say "Hi ${firstName}", "Hello", or any greeting
- Simply continue the conversation naturally
- If you must acknowledge, just say "I'm here" or "What's next?"`;
      } else {
        greetingInstruction = firstName
          ? `This is the FIRST connection. Greet once: "Hi ${firstName}!" - but NEVER re-greet after this.`
          : `This is the FIRST connection. Give a brief warm greeting - but NEVER re-greet after this.`;
      }

      // Build page context section
      let pageContextSection = "";
      if (pageContext?.pageType === 'coaching') {
        pageContextSection = `
PAGE_CONTEXT: COACHING PAGE
The user is interested in executive coaching services.
Help them find coaches, understand coaching benefits, and schedule sessions.
`;
      } else if (pageContext?.location) {
        pageContextSection = `
PAGE_CONTEXT: JOBS PAGE
User is viewing: ${pageContext.location.toUpperCase()} context
${pageContext.totalJobs ? `- Total jobs available: ${pageContext.totalJobs}` : ''}
When they say "jobs here" or "these roles" → they mean ${pageContext.location}.
`;
      }

      const systemPrompt = `## YOUR ROLE
You are the VOICE INTERFACE for a fractional executive career platform.
Help users with onboarding, finding jobs, and booking coaching sessions.

## USER PROFILE
${firstName ? `Name: ${firstName}` : 'Guest user'}
${zepContext ? `\n### What I Remember About ${firstName || 'You'}:\n${zepContext}\n` : '\n### No prior history - this is their first visit.\n'}

${pageContextSection}

## GREETING RULES
${greetingInstruction}

## BEHAVIOR GUIDELINES
1. Keep responses SHORT for voice - 1-2 sentences max unless asked for details
2. Be helpful and conversational
3. When they express interest, confirm and remember it
4. Use the search_jobs tool when they ask about job opportunities
`;

      // Use stable session ID based on user ID
      const stableSessionId = userId
        ? `deep_fractional_${userId}`
        : `deep_fractional_anon_${Math.random().toString(36).slice(2, 10)}`;

      // Include page context in session ID for CLM (format: "firstName|sessionId|location:X,jobs:Y")
      let pageContextPart = '';
      if (pageContext?.pageType === 'coaching') {
        pageContextPart = `|pageType:coaching`;
      } else if (pageContext?.location) {
        const parts = [`location:${pageContext.location}`];
        if (pageContext.totalJobs) parts.push(`jobs:${pageContext.totalJobs}`);
        pageContextPart = `|${parts.join(',')}`;
      }

      const customSessionId = firstName
        ? `${firstName}|${stableSessionId}${pageContextPart}`
        : `|${stableSessionId}${pageContextPart}`;

      // IMPORTANT: CLM (Custom Language Model) URL must be configured in Hume Dashboard
      // Config ID: 5900eabb-8de1-42cf-ba18-3a718257b3e7
      // CLM URL should be: https://agent.fractional.quest/chat/completions
      // See: https://dev.hume.ai/docs/speech-to-speech-evi/guides/custom-language-model
      const configId = process.env.NEXT_PUBLIC_HUME_CONFIG_ID;

      console.log("[VOICE] Got token, connecting with session:", customSessionId);
      console.log("[VOICE] Quick reconnect?", isQuickReconnect, "Was greeted?", wasGreeted);
      console.log("[VOICE] User authenticated:", !!userId, "userId:", userId || 'anonymous');
      console.log("[VOICE] Using Hume config:", configId || 'default');
      console.log("[VOICE] NOTE: CLM endpoint must be configured in Hume Dashboard for this config");

      // Connect with token auth and session settings
      // CLM URL is configured in Hume Dashboard, not here in code
      await connect({
        auth: { type: "accessToken", value: accessToken },
        ...(configId && { configId }),
        sessionSettings: {
          type: "session_settings",
          systemPrompt: systemPrompt,
          customSessionId: customSessionId,
        }
      });

      console.log("[VOICE] Connect call completed");

      // Mark that we've greeted this session (only trigger greeting on FIRST connection)
      if (!wasGreeted && !isQuickReconnect && firstName) {
        setTimeout(() => {
          console.log("[VOICE] FIRST connection - triggering greeting for:", firstName);
          greetedThisSession.current = true;
          setSessionValue(SESSION_GREETED_KEY, true);
          sendUserInput(`Hello, my name is ${firstName}`);
        }, 500);
      } else {
        // RECONNECTION - do NOT send any input, just mark as greeted
        console.log("[VOICE] RECONNECTION detected - NOT re-greeting");
        greetedThisSession.current = true;
        setSessionValue(SESSION_GREETED_KEY, true);
      }
    } catch (err) {
      console.error("[VOICE] Connection error:", err);
      setError(err instanceof Error ? err.message : "Failed to connect");
    } finally {
      setIsConnecting(false);
    }
  }, [connect, firstName, userId, pageContext, sendUserInput]);

  // Disconnect
  const handleDisconnect = useCallback(() => {
    // Track disconnect time for returning user detection
    const now = Date.now();
    lastInteractionTime.current = now;
    setSessionValue(SESSION_LAST_INTERACTION_KEY, now);
    disconnect();
    lastSentMsgId.current = null;
  }, [disconnect]);

  // Determine button state
  const isConnected = status.value === "connected";
  const isActive = isConnected || isConnecting;

  return (
    <div className="flex items-center gap-2">
      <button
        onClick={isActive ? handleDisconnect : handleConnect}
        disabled={isConnecting}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-full font-medium text-sm
          transition-all duration-200 shadow-sm
          ${isActive
            ? "bg-red-500 hover:bg-red-600 text-white"
            : "bg-indigo-600 hover:bg-indigo-700 text-white"
          }
          ${isConnecting ? "opacity-70 cursor-wait" : ""}
        `}
        aria-label={isActive ? "Stop voice" : "Start voice"}
      >
        {/* Microphone icon */}
        <svg
          className={`w-5 h-5 ${isConnected ? "animate-pulse" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          {isActive ? (
            // Stop icon
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z"
            />
          ) : (
            // Microphone icon
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z"
            />
          )}
        </svg>
        <span>
          {isConnecting
            ? "Connecting..."
            : isConnected
            ? "Stop Voice"
            : "Voice Chat"}
        </span>
      </button>

      {/* Status indicator */}
      {isConnected && (
        <div className="flex items-center gap-1 text-xs text-green-600">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Listening
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="text-xs text-red-500">{error}</div>
      )}
    </div>
  );
}

// Stable callbacks to prevent VoiceProvider remounting
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleVoiceError = (err: any) => console.error("[VOICE] Provider error:", err?.message || err);
const handleVoiceOpen = () => console.log("[VOICE] Connection opened");
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const handleVoiceClose = (e: any) => console.log("[VOICE] Connection closed:", e?.code, e?.reason);

/**
 * Voice input component with Hume EVI integration.
 *
 * Requires environment variables:
 * - HUME_API_KEY and HUME_SECRET_KEY (server-side for token generation)
 * - NEXT_PUBLIC_HUME_CONFIG_ID (optional, for Hume config)
 */
export function VoiceInput({ onMessage, firstName, userId, pageContext }: VoiceInputProps) {
  return (
    <VoiceProvider
      onError={handleVoiceError}
      onOpen={handleVoiceOpen}
      onClose={handleVoiceClose}
    >
      <VoiceButton
        onMessage={onMessage}
        firstName={firstName}
        userId={userId}
        pageContext={pageContext}
      />
    </VoiceProvider>
  );
}

export default VoiceInput;
