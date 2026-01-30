import type { Metadata } from "next";
import { CopilotKit } from "@copilotkit/react-core";
import { UserButton } from "@neondatabase/auth/react";
import { Providers } from "@/components/providers";
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
        <Providers>
          <CopilotKit
            runtimeUrl="/api/copilotkit"
            agent="fractional_quest"
          >
            <header className="fixed top-0 right-0 p-4 z-50">
              <UserButton size="icon" />
            </header>
            {children}
          </CopilotKit>
        </Providers>
      </body>
    </html>
  );
}
