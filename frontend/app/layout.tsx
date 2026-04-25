import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NEXUS — AI Task Execution Agent",
  description:
    "Autonomous multi-step task execution engine with real-time streaming, self-healing recovery, and human-in-the-loop breakpoints.",
  keywords: ["AI", "Task Execution", "Agent", "LLM", "Automation"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
