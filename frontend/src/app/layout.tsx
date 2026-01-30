import type { Metadata } from "next";
import { CopilotKit } from "@copilotkit/react-core";
import { NeonAuthUIProvider, UserButton } from "@neondatabase/auth/react";
import { authClient } from "@/lib/auth/client";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import "@neondatabase/auth-ui/css";

export const metadata: Metadata = {
  title: "Fractional Quest | Deep Agents",
  description: "AI-powered career assistant for fractional executives",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">
        <NeonAuthUIProvider
          authClient={authClient as any}
          redirectTo="/"
          emailOTP
          socialProviders={["google"]}
        >
          <CopilotKit
            runtimeUrl="/api/copilotkit"
            agent="fractional_quest"
          >
            <header className="fixed top-0 right-0 p-4 z-50">
              <UserButton size="icon" />
            </header>
            {children}
          </CopilotKit>
        </NeonAuthUIProvider>
      </body>
    </html>
  );
}
