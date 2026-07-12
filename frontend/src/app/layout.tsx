import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "react-hot-toast";

export const metadata: Metadata = {
  title: "StudyPilot - AI Study & Exam Readiness",
  description: "AI-powered study tracking and exam readiness platform for college students",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
