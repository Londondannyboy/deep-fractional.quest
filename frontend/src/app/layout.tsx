import type { Metadata } from "next";
import { CopilotKit } from "@copilotkit/react-core";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";

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
    <html lang="en">
      <body className="antialiased">
        <CopilotKit
          runtimeUrl="/api/copilotkit"
          agent="fractional_quest"
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
