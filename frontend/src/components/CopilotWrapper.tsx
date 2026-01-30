"use client";

import { CopilotKit } from "@copilotkit/react-core";
import { authClient } from "@/lib/auth/client";
import { useMemo } from "react";

interface CopilotWrapperProps {
  children: React.ReactNode;
}

/**
 * Client-side CopilotKit wrapper that provides user-based thread ID.
 *
 * This ensures Voice and Chat share the same thread ID pattern:
 * - Authenticated users: `deep_fractional_${userId}`
 * - Anonymous users: undefined (CopilotKit generates one)
 *
 * This enables conversation continuity between Voice and Chat
 * since both use the same checkpointed thread.
 */
export function CopilotWrapper({ children }: CopilotWrapperProps) {
  const { data: session } = authClient.useSession();
  const userId = session?.user?.id;

  // Generate consistent thread ID matching Voice's pattern
  // Voice uses: `deep_fractional_${userId}` as threadId
  const threadId = useMemo(() => {
    if (userId) {
      return `deep_fractional_${userId}`;
    }
    return undefined; // Let CopilotKit generate for anonymous
  }, [userId]);

  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="fractional_quest"
      threadId={threadId}
    >
      {children}
    </CopilotKit>
  );
}
