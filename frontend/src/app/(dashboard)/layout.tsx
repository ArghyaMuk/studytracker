"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { useAuthStore } from "@/lib/store";
import { userApi } from "@/lib/api";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const { user, setUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      router.replace("/login");
      return;
    }

    if (!user) {
      // Decode user ID from token
      try {
        const payload = JSON.parse(atob(token.split(".")[1]));
        const userId = parseInt(payload.sub);
        userApi.getProfile(userId).then(({ data }) => setUser(data));
      } catch {
        router.replace("/login");
      }
    }
  }, [user, setUser, router]);

  if (!isAuthenticated && typeof window !== "undefined" && !localStorage.getItem("access_token")) {
    return null;
  }

  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <main className="flex-1 p-8 overflow-auto">{children}</main>
    </div>
  );
}
