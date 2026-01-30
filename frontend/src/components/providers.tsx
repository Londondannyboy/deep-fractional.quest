'use client';

import { NeonAuthUIProvider } from '@neondatabase/auth/react';
import { authClient } from '@/lib/auth/client';

// Auth provider with Google OAuth enabled
// CopilotKit wraps this in layout.tsx
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NeonAuthUIProvider
      authClient={authClient as any}
      redirectTo="/"
      social={{ providers: ['google'] }}
    >
      {children}
    </NeonAuthUIProvider>
  );
}
