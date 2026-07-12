"use client";

import { useEffect, useState } from "react";
import { Plus, Clock, Star, BookOpen } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/store";
import { sessionApi } from "@/lib/api";

interface Session {
  id: number;
  subject_code: string;
  unit_number: number;
  started_at: string;
  duration_min: number;
  focus_rating: number;
  notes: string | null;
}

export default function SessionsPage() {
  const user = useAuthStore((s) => s.user);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    subject_code: "",
    unit_number: 1,
    duration_min: 30,
    focus_rating: 3,
    notes: "",
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!user) return;
    sessionApi.list(user.id).then(({ data }) => setSessions(data)).catch(() => {});
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setLoading(true);
    try {
      const { data } = await sessionApi.create(user.id, {
        ...form,
        notes: form.notes || undefined,
      });
      setSessions([data, ...sessions]);
      setShowForm(false);
      setForm({ subject_code: "", unit_number: 1, duration_min: 30, focus_rating: 3, notes: "" });
      toast.success("Session logged!");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to log session";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await sessionApi.delete(id);
      setSessions(sessions.filter((s) => s.id !== id));
      toast.success("Session deleted");
    } catch {
      toast.error("Delete failed");
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Study Sessions</h1>
          <p className="text-gray-500 mt-1">Log and track your study activity</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
        >
          <Plus size={18} /> Log Session
        </button>
      </div>

      {showForm && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">New Study Session</h2>
          <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject Code</label>
              <input
                type="text"
                required
                value={form.subject_code}
                onChange={(e) => setForm({ ...form, subject_code: e.target.value })}
                placeholder="e.g. CS301"
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Unit Number</label>
              <input
                type="number"
                required
                min={1}
                value={form.unit_number}
                onChange={(e) => setForm({ ...form, unit_number: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Duration (minutes)
              </label>
              <input
                type="number"
                required
                min={1}
                max={480}
                value={form.duration_min}
                onChange={(e) => setForm({ ...form, duration_min: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Focus Rating (1-5)
              </label>
              <div className="flex gap-2 mt-1">
                {[1, 2, 3, 4, 5].map((r) => (
                  <button
                    key={r}
                    type="button"
                    onClick={() => setForm({ ...form, focus_rating: r })}
                    className={`w-10 h-10 rounded-lg border flex items-center justify-center transition-colors ${
                      form.focus_rating >= r
                        ? "bg-yellow-400 border-yellow-500 text-white"
                        : "border-gray-300 text-gray-400"
                    }`}
                  >
                    <Star size={16} fill={form.focus_rating >= r ? "white" : "none"} />
                  </button>
                ))}
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes (optional)</label>
              <textarea
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                maxLength={1000}
                rows={2}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 text-gray-900"
              />
            </div>
            <div className="md:col-span-2">
              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
              >
                {loading ? "Saving..." : "Save Session"}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="space-y-3">
        {sessions.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center shadow-sm border border-gray-100">
            <BookOpen className="mx-auto text-gray-300 mb-3" size={40} />
            <p className="text-gray-500">No sessions logged yet. Start tracking your study time!</p>
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.id}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100 flex items-center justify-between"
            >
              <div className="flex items-center gap-4">
                <div className="p-2 bg-indigo-50 rounded-lg">
                  <BookOpen size={20} className="text-indigo-600" />
                </div>
                <div>
                  <div className="font-medium text-gray-900">
                    {session.subject_code} — Unit {session.unit_number}
                  </div>
                  <div className="text-sm text-gray-500 mt-0.5 flex items-center gap-3">
                    <span className="flex items-center gap-1">
                      <Clock size={12} /> {session.duration_min} min
                    </span>
                    <span className="flex items-center gap-1">
                      <Star size={12} fill="gold" className="text-yellow-500" />{" "}
                      {session.focus_rating}/5
                    </span>
                    <span>
                      {new Date(session.started_at).toLocaleDateString()}
                    </span>
                  </div>
                  {session.notes && (
                    <p className="text-xs text-gray-400 mt-1">{session.notes}</p>
                  )}
                </div>
              </div>
              <button
                onClick={() => handleDelete(session.id)}
                className="text-sm text-red-500 hover:text-red-700"
              >
                Delete
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
