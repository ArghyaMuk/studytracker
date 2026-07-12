"use client";

import { useEffect, useState } from "react";
import { BookOpen, Brain, Calendar, TrendingUp } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { readinessApi, revisionApi, sessionApi } from "@/lib/api";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className="text-2xl font-bold mt-1 text-gray-900">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>{icon}</div>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user);
  const [stats, setStats] = useState({
    sessionsToday: 0,
    dueRevisions: 0,
    avgReadiness: 0,
    studyStreak: 0,
  });
  const [revisionItems, setRevisionItems] = useState<Array<{
    id: number;
    subject_code: string;
    unit_number: number;
    next_review_date: string;
  }>>([]);

  useEffect(() => {
    if (!user) return;

    const load = async () => {
      try {
        const [sessionsRes, revisionRes, readinessRes] = await Promise.allSettled([
          sessionApi.list(user.id),
          revisionApi.getToday(user.id),
          readinessApi.getAll(user.id),
        ]);

        const sessions = sessionsRes.status === "fulfilled" ? sessionsRes.value.data : [];
        const revisions = revisionRes.status === "fulfilled" ? revisionRes.value.data : [];
        const readiness = readinessRes.status === "fulfilled" ? readinessRes.value.data : [];

        const today = new Date().toDateString();
        const sessionsToday = sessions.filter(
          (s: { started_at: string }) => new Date(s.started_at).toDateString() === today
        ).length;

        const avgScore =
          readiness.length > 0
            ? Math.round(
                readiness.reduce((sum: number, r: { score: number }) => sum + r.score, 0) /
                  readiness.length
              )
            : 0;

        setStats({
          sessionsToday,
          dueRevisions: revisions.length,
          avgReadiness: avgScore,
          studyStreak: sessions.length > 0 ? Math.min(sessions.length, 7) : 0,
        });
        setRevisionItems(revisions.slice(0, 5));
      } catch {
        // Silently fail on dashboard load
      }
    };

    load();
  }, [user]);

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user?.name ? `, ${user.name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-gray-500 mt-1">
          Semester {user?.current_semester || "—"} • Here&apos;s your study overview
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard
          title="Sessions Today"
          value={stats.sessionsToday}
          icon={<BookOpen size={20} className="text-blue-600" />}
          color="bg-blue-50"
        />
        <StatCard
          title="Due for Revision"
          value={stats.dueRevisions}
          icon={<Calendar size={20} className="text-orange-600" />}
          color="bg-orange-50"
        />
        <StatCard
          title="Avg Readiness"
          value={`${stats.avgReadiness}%`}
          icon={<TrendingUp size={20} className="text-green-600" />}
          color="bg-green-50"
        />
        <StatCard
          title="Study Streak"
          value={`${stats.studyStreak} days`}
          icon={<Brain size={20} className="text-purple-600" />}
          color="bg-purple-50"
        />
      </div>

      {/* Today's Revision */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Today&apos;s Revision Plan</h2>
        {revisionItems.length === 0 ? (
          <p className="text-gray-500 text-sm">No items due for revision today. Keep it up!</p>
        ) : (
          <div className="space-y-3">
            {revisionItems.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <span className="font-medium text-gray-900">{item.subject_code}</span>
                  <span className="text-gray-500 ml-2">Unit {item.unit_number}</span>
                </div>
                <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded-full">
                  Due today
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
