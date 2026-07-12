"use client";

import { useEffect, useState } from "react";
import { BarChart3, TrendingUp, TrendingDown } from "lucide-react";
import { useAuthStore } from "@/lib/store";
import { readinessApi } from "@/lib/api";

interface ReadinessScore {
  subject_code: string;
  unit_number: number | null;
  score: number;
  computed_at: string | null;
  breakdown_json: string | null;
}

function ScoreBar({ score, label }: { score: number; label: string }) {
  const color =
    score >= 75 ? "bg-green-500" : score >= 50 ? "bg-yellow-500" : score >= 25 ? "bg-orange-500" : "bg-red-500";
  return (
    <div className="flex items-center gap-3">
      <span className="text-sm text-gray-600 w-20 shrink-0">{label}</span>
      <div className="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-sm font-semibold text-gray-900 w-12 text-right">{score}%</span>
    </div>
  );
}

export default function ReadinessPage() {
  const user = useAuthStore((s) => s.user);
  const [scores, setScores] = useState<ReadinessScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    readinessApi
      .getAll(user.id)
      .then(({ data }) => setScores(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-gray-400">Computing readiness scores...</div>
      </div>
    );
  }

  // Separate subject-level (unit_number = null) and unit-level scores
  const subjectScores = scores.filter((s) => s.unit_number === null);
  const unitScores = scores.filter((s) => s.unit_number !== null);

  // Group unit scores by subject
  const unitsBySubject: Record<string, ReadinessScore[]> = {};
  unitScores.forEach((u) => {
    if (!unitsBySubject[u.subject_code]) unitsBySubject[u.subject_code] = [];
    unitsBySubject[u.subject_code].push(u);
  });

  const avgScore =
    subjectScores.length > 0
      ? Math.round(subjectScores.reduce((sum, s) => sum + s.score, 0) / subjectScores.length)
      : 0;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Exam Readiness</h1>
        <p className="text-gray-500 mt-1">Track your preparedness across all subjects</p>
      </div>

      {/* Overall Score */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6">
        <div className="flex items-center gap-4">
          <div className={`p-4 rounded-xl ${avgScore >= 60 ? "bg-green-50" : "bg-orange-50"}`}>
            {avgScore >= 60 ? (
              <TrendingUp size={28} className="text-green-600" />
            ) : (
              <TrendingDown size={28} className="text-orange-600" />
            )}
          </div>
          <div>
            <p className="text-sm text-gray-500">Overall Readiness</p>
            <p className="text-3xl font-bold text-gray-900">{avgScore}%</p>
          </div>
          <div className="ml-auto text-right">
            <p className="text-sm text-gray-500">{subjectScores.length} subjects tracked</p>
          </div>
        </div>
      </div>

      {subjectScores.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center shadow-sm border border-gray-100">
          <BarChart3 className="mx-auto text-gray-300 mb-3" size={40} />
          <p className="text-gray-500">
            No readiness scores yet. Log study sessions and take quizzes to build your scores.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {subjectScores.map((subject) => (
            <div
              key={subject.subject_code}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">{subject.subject_code}</h3>
                <span
                  className={`text-sm font-bold px-2 py-0.5 rounded ${
                    subject.score >= 75
                      ? "bg-green-100 text-green-700"
                      : subject.score >= 50
                      ? "bg-yellow-100 text-yellow-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {subject.score}%
                </span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5 mb-3">
                <div
                  className={`h-full rounded-full transition-all ${
                    subject.score >= 75
                      ? "bg-green-500"
                      : subject.score >= 50
                      ? "bg-yellow-500"
                      : "bg-red-500"
                  }`}
                  style={{ width: `${subject.score}%` }}
                />
              </div>
              {/* Unit breakdown */}
              {unitsBySubject[subject.subject_code] && (
                <div className="space-y-2 mt-3 pl-2 border-l-2 border-gray-100">
                  {unitsBySubject[subject.subject_code]
                    .sort((a, b) => (a.unit_number || 0) - (b.unit_number || 0))
                    .map((unit) => (
                      <ScoreBar
                        key={`${unit.subject_code}-${unit.unit_number}`}
                        score={unit.score}
                        label={`Unit ${unit.unit_number}`}
                      />
                    ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
