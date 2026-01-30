import type { Metadata } from "next";
import { UserButton } from "@neondatabase/auth/react";
import { Providers } from "@/components/providers";
import { CopilotWrapper } from "@/components/CopilotWrapper";
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
          <CopilotWrapper>
            <header className="fixed top-0 right-0 p-4 z-50">
              <UserButton size="icon" />
            </header>
            {children}
          </CopilotWrapper>
        </Providers>
      </body>
    </html>
  );
}
