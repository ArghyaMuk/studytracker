"use client";

import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/store";
import { userApi, notificationApi, curriculumApi } from "@/lib/api";
import api from "@/lib/api";
import { Trash2, Users, Database, RefreshCw } from "lucide-react";

interface UserListItem {
  id: number;
  name: string;
  email: string;
  college: string | null;
  current_semester: number | null;
}

export default function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const isAdmin = user?.email === "admin@studypilot.com";

  const [profile, setProfile] = useState({
    name: "",
    college: "",
    university: "",
    current_semester: 1,
    daily_study_hours_target: 2,
    goal_type: "semester_exam",
  });
  const [notifPrefs, setNotifPrefs] = useState({
    daily_digest_enabled: true,
    readiness_alert_enabled: true,
    exam_countdown_enabled: true,
    inactivity_nudge_enabled: true,
    preferred_time: "08:00",
  });
  const [saving, setSaving] = useState(false);

  // Admin-specific state
  const [platformStats, setPlatformStats] = useState({
    totalPrograms: 0,
    totalSubjects: 0,
    servicesHealthy: 0,
    servicesTotal: 7,
  });
  const [healthStatus, setHealthStatus] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!user) return;
    setProfile({
      name: user.name || "",
      college: user.college || "",
      university: user.university || "",
      current_semester: user.current_semester || 1,
      daily_study_hours_target: user.daily_study_hours_target || 2,
      goal_type: user.goal_type || "semester_exam",
    });

    notificationApi
      .getPreferences(user.id)
      .then(({ data }) => {
        setNotifPrefs({
          daily_digest_enabled: data.daily_digest_enabled,
          readiness_alert_enabled: data.readiness_alert_enabled,
          exam_countdown_enabled: data.exam_countdown_enabled,
          inactivity_nudge_enabled: data.inactivity_nudge_enabled,
          preferred_time: data.preferred_time || "08:00",
        });
      })
      .catch(() => {});

    // Load admin stats
    if (isAdmin) {
      loadAdminData();
    }
  }, [user, isAdmin]);

  const loadAdminData = async () => {
    try {
      const [programsRes, healthRes] = await Promise.allSettled([
        curriculumApi.getPrograms(),
        fetch("http://localhost:8000/health").then((r) => r.json()),
      ]);

      if (programsRes.status === "fulfilled") {
        setPlatformStats((s) => ({ ...s, totalPrograms: programsRes.value.data.length }));
      }
      if (healthRes.status === "fulfilled") {
        const health = healthRes.value;
        setHealthStatus(health.services || {});
        const healthy = Object.values(health.services || {}).filter((s) => s === "healthy").length;
        setPlatformStats((s) => ({
          ...s,
          servicesHealthy: healthy,
          servicesTotal: Object.keys(health.services || {}).length,
        }));
      }
    } catch {
      // silently fail
    }
  };

  const saveProfile = async () => {
    if (!user) return;
    setSaving(true);
    try {
      const { data } = await userApi.updateProfile(user.id, profile);
      setUser(data);
      toast.success("Profile updated");
    } catch {
      toast.error("Failed to update profile");
    } finally {
      setSaving(false);
    }
  };

  const saveNotifications = async () => {
    if (!user) return;
    setSaving(true);
    try {
      await notificationApi.updatePreferences(user.id, notifPrefs);
      toast.success("Notification preferences saved");
    } catch {
      toast.error("Failed to save preferences");
    } finally {
      setSaving(false);
    }
  };

  // Admin settings view
  if (isAdmin) {
    return (
      <div>
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Admin Settings</h1>
          <p className="text-gray-500 mt-1">Platform configuration and management</p>
        </div>

        <div className="space-y-6 max-w-4xl">
          {/* Platform Health */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Database size={18} /> Platform Health
              </h2>
              <button
                onClick={loadAdminData}
                className="p-2 text-gray-400 hover:text-indigo-600 rounded-lg hover:bg-gray-50"
              >
                <RefreshCw size={16} />
              </button>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="p-3 bg-green-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-700">
                  {platformStats.servicesHealthy}/{platformStats.servicesTotal}
                </div>
                <div className="text-xs text-green-600">Services Healthy</div>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-700">{platformStats.totalPrograms}</div>
                <div className="text-xs text-blue-600">Programs</div>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-700">3</div>
                <div className="text-xs text-purple-600">Databases</div>
              </div>
              <div className="p-3 bg-orange-50 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-700">Active</div>
                <div className="text-xs text-orange-600">RabbitMQ</div>
              </div>
            </div>
            {/* Service status list */}
            <div className="space-y-2">
              {Object.entries(healthStatus).map(([name, status]) => (
                <div key={name} className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                  <span className="text-sm text-gray-700 font-mono">{name}</span>
                  <span
                    className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      status === "healthy"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {status}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Admin Profile */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Admin Profile</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  type="text"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="text"
                  disabled
                  value={user?.email || ""}
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-gray-500 bg-gray-50"
                />
              </div>
            </div>
            <button
              onClick={saveProfile}
              disabled={saving}
              className="mt-4 px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Profile"}
            </button>
          </div>

          {/* Platform Configuration */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Platform Configuration</h2>
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Daily Study Target (hrs)
                  </label>
                  <input
                    type="number"
                    min={0.5}
                    max={16}
                    step={0.5}
                    value={profile.daily_study_hours_target}
                    onChange={(e) =>
                      setProfile({ ...profile, daily_study_hours_target: parseFloat(e.target.value) })
                    }
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Default Goal Type
                  </label>
                  <select
                    value={profile.goal_type}
                    onChange={(e) => setProfile({ ...profile, goal_type: e.target.value })}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                  >
                    <option value="semester_exam">Semester Exams</option>
                    <option value="placement_prep">Placement Prep</option>
                    <option value="competitive_exam">Competitive Exam</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Gateway URL
                </label>
                <input
                  type="text"
                  disabled
                  value="http://localhost:8000"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-gray-500 bg-gray-50 font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  JWT Secret Key
                </label>
                <input
                  type="password"
                  disabled
                  value="••••••••••••••••••••"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-lg text-gray-500 bg-gray-50"
                />
              </div>
            </div>
          </div>

          {/* Notification Defaults (Admin can modify global defaults) */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Global Notification Defaults
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              These settings apply as defaults for new students.
            </p>
            <div className="space-y-3">
              {[
                { key: "daily_digest_enabled", label: "Daily Study Digest" },
                { key: "readiness_alert_enabled", label: "Readiness Drop Alerts" },
                { key: "exam_countdown_enabled", label: "Exam Countdown Reminders" },
                { key: "inactivity_nudge_enabled", label: "Inactivity Nudges (48h)" },
              ].map(({ key, label }) => (
                <label
                  key={key}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer"
                >
                  <span className="text-sm text-gray-700">{label}</span>
                  <input
                    type="checkbox"
                    checked={(notifPrefs as Record<string, boolean | string>)[key] as boolean}
                    onChange={(e) => setNotifPrefs({ ...notifPrefs, [key]: e.target.checked })}
                    className="h-4 w-4 text-indigo-600 rounded"
                  />
                </label>
              ))}
              <div className="p-3 bg-gray-50 rounded-lg">
                <label className="block text-sm text-gray-700 mb-1">Default Delivery Time</label>
                <input
                  type="time"
                  value={notifPrefs.preferred_time}
                  onChange={(e) => setNotifPrefs({ ...notifPrefs, preferred_time: e.target.value })}
                  className="px-3 py-2 border border-gray-300 rounded-lg text-gray-900"
                />
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <label className="block text-sm text-gray-700 mb-1">Max Notifications Per Day</label>
                <input
                  type="number"
                  disabled
                  value={10}
                  className="px-3 py-2 border border-gray-200 rounded-lg text-gray-500 bg-white w-24"
                />
                <span className="text-xs text-gray-400 ml-2">per student</span>
              </div>
            </div>
            <button
              onClick={saveNotifications}
              disabled={saving}
              className="mt-4 px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              {saving ? "Saving..." : "Save Notification Defaults"}
            </button>
          </div>

          {/* Danger Zone */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-red-200">
            <h2 className="text-lg font-semibold text-red-700 mb-4">Danger Zone</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Reset All Readiness Scores</p>
                  <p className="text-xs text-gray-500">
                    Clears cached readiness scores for all students
                  </p>
                </div>
                <button
                  onClick={() => toast.error("This action requires confirmation in production")}
                  className="px-3 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded-lg hover:bg-red-200"
                >
                  Reset
                </button>
              </div>
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Clear Event Queue</p>
                  <p className="text-xs text-gray-500">
                    Purges all pending events from RabbitMQ
                  </p>
                </div>
                <button
                  onClick={() => toast.error("This action requires confirmation in production")}
                  className="px-3 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded-lg hover:bg-red-200"
                >
                  Purge
                </button>
              </div>
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-900">Flush Redis Cache</p>
                  <p className="text-xs text-gray-500">
                    Clears all cached data (tokens, rate limits, scores)
                  </p>
                </div>
                <button
                  onClick={() => toast.error("This action requires confirmation in production")}
                  className="px-3 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded-lg hover:bg-red-200"
                >
                  Flush
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Student/Test user settings view
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Manage your profile and preferences</p>
      </div>

      <div className="space-y-6 max-w-2xl">
        {/* Profile Section */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Profile</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={profile.name}
                onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">College</label>
              <input
                type="text"
                value={profile.college}
                onChange={(e) => setProfile({ ...profile, college: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">University</label>
              <input
                type="text"
                value={profile.university}
                onChange={(e) => setProfile({ ...profile, university: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Semester</label>
              <select
                value={profile.current_semester}
                onChange={(e) => setProfile({ ...profile, current_semester: parseInt(e.target.value) })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              >
                {[1, 2, 3, 4, 5, 6, 7, 8].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Daily Study Target (hrs)
              </label>
              <input
                type="number"
                min={0.5}
                max={16}
                step={0.5}
                value={profile.daily_study_hours_target}
                onChange={(e) =>
                  setProfile({ ...profile, daily_study_hours_target: parseFloat(e.target.value) })
                }
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Goal Type</label>
              <select
                value={profile.goal_type}
                onChange={(e) => setProfile({ ...profile, goal_type: e.target.value })}
                className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
              >
                <option value="semester_exam">Semester Exams</option>
                <option value="placement_prep">Placement Prep</option>
                <option value="competitive_exam">Competitive Exam</option>
              </select>
            </div>
          </div>
          <button
            onClick={saveProfile}
            disabled={saving}
            className="mt-4 px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </div>

        {/* Notification Preferences */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Notifications</h2>
          <div className="space-y-3">
            {[
              { key: "daily_digest_enabled", label: "Daily Study Digest" },
              { key: "readiness_alert_enabled", label: "Readiness Drop Alerts" },
              { key: "exam_countdown_enabled", label: "Exam Countdown Reminders" },
              { key: "inactivity_nudge_enabled", label: "Inactivity Nudges" },
            ].map(({ key, label }) => (
              <label
                key={key}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg cursor-pointer"
              >
                <span className="text-sm text-gray-700">{label}</span>
                <input
                  type="checkbox"
                  checked={(notifPrefs as Record<string, boolean | string>)[key] as boolean}
                  onChange={(e) => setNotifPrefs({ ...notifPrefs, [key]: e.target.checked })}
                  className="h-4 w-4 text-indigo-600 rounded"
                />
              </label>
            ))}
            <div className="p-3 bg-gray-50 rounded-lg">
              <label className="block text-sm text-gray-700 mb-1">Preferred Delivery Time</label>
              <input
                type="time"
                value={notifPrefs.preferred_time}
                onChange={(e) => setNotifPrefs({ ...notifPrefs, preferred_time: e.target.value })}
                className="px-3 py-2 border border-gray-300 rounded-lg text-gray-900"
              />
            </div>
          </div>
          <button
            onClick={saveNotifications}
            disabled={saving}
            className="mt-4 px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save Preferences"}
          </button>
        </div>
      </div>
    </div>
  );
}
