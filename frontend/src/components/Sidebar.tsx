"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  BookOpen,
  Brain,
  BarChart3,
  Calendar,
  Settings,
  LogOut,
  ShieldCheck,
} from "lucide-react";
import { useAuthStore } from "@/lib/store";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/sessions", label: "Study Sessions", icon: BookOpen },
  { href: "/quizzes", label: "Quizzes", icon: Brain },
  { href: "/revision", label: "Revision", icon: Calendar },
  { href: "/readiness", label: "Readiness", icon: BarChart3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

const adminItems = [
  { href: "/admin", label: "Courses (Admin)", icon: ShieldCheck },
];

export default function Sidebar() {
  const pathname = usePathname();
  const logout = useAuthStore((s) => s.logout);
  const user = useAuthStore((s) => s.user);

  const isAdmin = user?.email === "admin@studypilot.com";
  const allNavItems = isAdmin ? [...navItems, ...adminItems] : navItems;

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col min-h-screen">
      <div className="p-6 border-b border-gray-800">
        <h1 className="text-xl font-bold text-indigo-400">StudyPilot</h1>
        <p className="text-xs text-gray-400 mt-1">Exam Readiness Platform</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {allNavItems.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                active
                  ? "bg-indigo-600 text-white"
                  : "text-gray-300 hover:bg-gray-800 hover:text-white"
              }`}
            >
              <item.icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800">
        <button
          onClick={() => {
            logout();
            window.location.href = "/login";
          }}
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-300 hover:bg-gray-800 hover:text-white w-full"
        >
          <LogOut size={18} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
