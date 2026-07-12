"use client";

import { useEffect, useState } from "react";
import { Calendar, CheckCircle } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/store";
import { revisionApi } from "@/lib/api";

interface ReviewItem {
  id: number;
  subject_code: string;
  unit_number: number;
  ease_factor: number;
  interval_days: number;
  repetitions: number;
  next_review_date: string;
  last_reviewed_at: string | null;
}

export default function RevisionPage() {
  const user = useAuthStore((s) => s.user);
  const [todayItems, setTodayItems] = useState<ReviewItem[]>([]);
  const [upcomingItems, setUpcomingItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    const load = async () => {
      try {
        const [todayRes, upcomingRes] = await Promise.all([
          revisionApi.getToday(user.id),
          revisionApi.getUpcoming(user.id, 7),
        ]);
        setTodayItems(todayRes.data);
        setUpcomingItems(upcomingRes.data.filter(
          (item: ReviewItem) => !todayRes.data.find((t: ReviewItem) => t.id === item.id)
        ));
      } catch {
        // Silently handle
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  const handleGrade = async (itemId: number, quality: number) => {
    try {
      await revisionApi.grade(itemId, quality);
      setTodayItems(todayItems.filter((item) => item.id !== itemId));
      toast.success("Revision recorded!");
    } catch {
      toast.error("Failed to grade");
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">Loading revision schedule...</div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Spaced Repetition</h1>
        <p className="text-gray-500 mt-1">Smart revision scheduling based on SM-2 algorithm</p>
      </div>

      {/* Today's Reviews */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Calendar size={20} className="text-orange-500" />
          Due Today ({todayItems.length})
        </h2>
        {todayItems.length === 0 ? (
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
            <CheckCircle size={32} className="mx-auto text-green-500 mb-2" />
            <p className="text-gray-500">All caught up! No reviews due today.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {todayItems.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-xl p-5 shadow-sm border border-gray-100"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span className="font-medium text-gray-900">{item.subject_code}</span>
                    <span className="text-gray-500 ml-2">Unit {item.unit_number}</span>
                    <div className="text-xs text-gray-400 mt-1">
                      Repetitions: {item.repetitions} • EF: {item.ease_factor.toFixed(2)}
                    </div>
                  </div>
                  <div className="flex gap-1">
                    {[
                      { q: 1, label: "Forgot", color: "bg-red-100 text-red-700 hover:bg-red-200" },
                      { q: 3, label: "Hard", color: "bg-yellow-100 text-yellow-700 hover:bg-yellow-200" },
                      { q: 4, label: "Good", color: "bg-blue-100 text-blue-700 hover:bg-blue-200" },
                      { q: 5, label: "Easy", color: "bg-green-100 text-green-700 hover:bg-green-200" },
                    ].map(({ q, label, color }) => (
                      <button
                        key={q}
                        onClick={() => handleGrade(item.id, q)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium ${color} transition-colors`}
                      >
                        {label}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Upcoming */}
      {upcomingItems.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Upcoming This Week</h2>
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Subject</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Unit</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Due Date</th>
                  <th className="text-left px-5 py-3 text-xs font-medium text-gray-500 uppercase">Interval</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {upcomingItems.map((item) => (
                  <tr key={item.id}>
                    <td className="px-5 py-3 text-sm font-medium text-gray-900">{item.subject_code}</td>
                    <td className="px-5 py-3 text-sm text-gray-600">Unit {item.unit_number}</td>
                    <td className="px-5 py-3 text-sm text-gray-600">{item.next_review_date}</td>
                    <td className="px-5 py-3 text-sm text-gray-600">{item.interval_days}d</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
