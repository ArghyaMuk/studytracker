"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, Trash2, ClipboardList, CheckCircle, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/store";
import api from "@/lib/api";

interface QuestionInput {
  question: string;
  options: string[];
  correct_answer: string;
  difficulty: string;
}

export default function AdminQuizzesPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);

  // Redirect non-admin
  if (user && user.email !== "admin@studypilot.com") {
    router.replace("/dashboard");
    return null;
  }

  const [subjectCode, setSubjectCode] = useState("");
  const [unitNumber, setUnitNumber] = useState(1);
  const [mode, setMode] = useState<"mcq" | "viva">("mcq");
  const [difficulty, setDifficulty] = useState("medium");
  const [generateCount, setGenerateCount] = useState(5);
  const [questions, setQuestions] = useState<QuestionInput[]>([
    { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
  ]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [savedQuizId, setSavedQuizId] = useState<number | null>(null);

  const addQuestion = () => {
    setQuestions([
      ...questions,
      { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
    ]);
  };

  const removeQuestion = (index: number) => {
    if (questions.length <= 1) return;
    setQuestions(questions.filter((_, i) => i !== index));
  };

  const updateQuestion = (index: number, field: string, value: string) => {
    const updated = [...questions];
    updated[index] = { ...updated[index], [field]: value };
    setQuestions(updated);
  };

  const updateOption = (qIndex: number, optIndex: number, value: string) => {
    const updated = [...questions];
    updated[qIndex].options[optIndex] = value;
    setQuestions(updated);
  };

  // Generate questions from Gemini AI
  const handleGenerateFromGemini = async () => {
    if (!subjectCode.trim()) {
      toast.error("Enter a subject code first");
      return;
    }
    if (!user) return;

    setGenerating(true);
    try {
      // Use the quiz generate endpoint which calls Gemini
      const { data: quiz } = await api.post(`/quizzes/generate?user_id=${user.id}`, {
        subject_code: subjectCode,
        unit_number: unitNumber,
        difficulty,
        count: generateCount,
        mode,
      });

      // Fetch the generated questions
      const { data: fullQuiz } = await api.get(`/quizzes/${quiz.id}`);

      if (fullQuiz.questions && fullQuiz.questions.length > 0) {
        const generatedQuestions: QuestionInput[] = fullQuiz.questions.map(
          (q: { question: string; options_json: string | null; correct_answer: string; difficulty: string }) => {
            let options = ["", "", "", ""];
            if (q.options_json) {
              try {
                options = JSON.parse(q.options_json);
              } catch {
                options = ["", "", "", ""];
              }
            }
            return {
              question: q.question,
              options,
              correct_answer: q.correct_answer || "A",
              difficulty: q.difficulty || difficulty,
            };
          }
        );
        setQuestions(generatedQuestions);
        toast.success(`${generatedQuestions.length} questions generated from Gemini AI!`);
      } else {
        toast.error("No questions were generated. Try again.");
      }
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to generate from Gemini";
      
      // If quota exceeded, offer blank template questions for manual entry
      if (msg.includes("quota") || msg.includes("429") || msg.includes("unavailable")) {
        toast.error("Gemini quota exceeded. Blank templates created — fill them in manually.");
        const blankQuestions: QuestionInput[] = Array.from({ length: generateCount }, (_, i) => ({
          question: "",
          options: ["", "", "", ""],
          correct_answer: "A",
          difficulty,
        }));
        setQuestions(blankQuestions);
      } else {
        toast.error(msg);
      }
    } finally {
      setGenerating(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    // Validate
    const emptyQ = questions.find((q) => !q.question.trim());
    if (emptyQ) {
      toast.error("All questions must have text");
      return;
    }

    if (mode === "mcq") {
      const emptyOpt = questions.find((q) => q.options.some((o) => !o.trim()));
      if (emptyOpt) {
        toast.error("All MCQ options must be filled");
        return;
      }
    }

    setLoading(true);
    try {
      const questionsPayload = questions.map((q) => ({
        question: q.question,
        options_json: mode === "mcq" ? JSON.stringify(q.options) : null,
        correct_answer: q.correct_answer,
        difficulty: q.difficulty,
      }));

      const { data } = await api.post(`/admin/quizzes/custom`, {
        subject_code: subjectCode,
        unit_number: unitNumber,
        mode,
        questions: questionsPayload,
      });

      setSavedQuizId(data.id);
      toast.success(`Custom quiz created with ${questions.length} questions!`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create quiz";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setQuestions([
      { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
    ]);
    setSavedQuizId(null);
    setSubjectCode("");
    setUnitNumber(1);
  };

  if (savedQuizId) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">Quiz Created!</h2>
          <p className="text-gray-500 mb-1">
            Subject: <span className="font-mono font-medium">{subjectCode}</span> — Unit{" "}
            {unitNumber}
          </p>
          <p className="text-gray-500 mb-6">
            {questions.length} question{questions.length > 1 ? "s" : ""} • Mode:{" "}
            {mode.toUpperCase()}
          </p>
          <button
            onClick={reset}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Create Another Quiz
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Create Custom Quiz</h1>
        <p className="text-gray-500 mt-1">
          Generate questions from Gemini AI or add them manually
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 max-w-4xl">
        {/* Quiz Info */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <ClipboardList size={18} /> Quiz Details
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Subject Code</label>
              <input
                type="text"
                required
                value={subjectCode}
                onChange={(e) => setSubjectCode(e.target.value)}
                placeholder="e.g. CS301"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Unit Number</label>
              <input
                type="number"
                min={1}
                max={20}
                value={unitNumber}
                onChange={(e) => setUnitNumber(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Mode</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value as "mcq" | "viva")}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
              >
                <option value="mcq">MCQ</option>
                <option value="viva">Viva Q&A</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Difficulty</label>
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
          </div>

          {/* Generate from Gemini */}
          <div className="mt-4 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-purple-900 flex items-center gap-2">
                  <Sparkles size={16} className="text-purple-600" />
                  Generate with Gemini AI
                </h3>
                <p className="text-xs text-purple-600 mt-0.5">
                  Auto-generate questions based on subject &amp; unit topics from curriculum
                </p>
              </div>
              <div className="flex items-center gap-2">
                <label className="text-xs text-purple-700">Questions:</label>
                <input
                  type="number"
                  min={1}
                  max={20}
                  value={generateCount}
                  onChange={(e) => setGenerateCount(parseInt(e.target.value))}
                  className="w-16 px-2 py-1.5 border border-purple-300 rounded-lg text-sm text-gray-900"
                />
                <button
                  type="button"
                  onClick={handleGenerateFromGemini}
                  disabled={generating || !subjectCode.trim()}
                  className="flex items-center gap-1.5 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 disabled:opacity-50 transition-colors"
                >
                  <Sparkles size={14} />
                  {generating ? "Generating..." : "Generate"}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Questions */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              Questions ({questions.length})
            </h2>
            <span className="text-xs text-gray-400">
              Edit generated questions or add your own below
            </span>
          </div>

          {questions.map((q, qIdx) => (
            <div
              key={qIdx}
              className="bg-white rounded-xl p-5 shadow-sm border border-gray-100"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold text-gray-700">Question {qIdx + 1}</h3>
                <div className="flex items-center gap-2">
                  <select
                    value={q.difficulty}
                    onChange={(e) => updateQuestion(qIdx, "difficulty", e.target.value)}
                    className="text-xs px-2 py-1 border border-gray-200 rounded text-gray-600"
                  >
                    <option value="easy">Easy</option>
                    <option value="medium">Medium</option>
                    <option value="hard">Hard</option>
                  </select>
                  <button
                    type="button"
                    onClick={() => removeQuestion(qIdx)}
                    className="p-1 text-red-400 hover:text-red-600"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <textarea
                required
                value={q.question}
                onChange={(e) => updateQuestion(qIdx, "question", e.target.value)}
                placeholder="Enter your question..."
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 mb-3"
              />

              {mode === "mcq" ? (
                <div className="space-y-2">
                  {q.options.map((opt, optIdx) => {
                    const letter = String.fromCharCode(65 + optIdx);
                    const isCorrect = q.correct_answer === letter;
                    return (
                      <div key={optIdx} className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={() => updateQuestion(qIdx, "correct_answer", letter)}
                          className={`w-7 h-7 rounded-full border text-xs font-bold flex items-center justify-center shrink-0 transition-colors ${
                            isCorrect
                              ? "bg-green-500 border-green-500 text-white"
                              : "border-gray-300 text-gray-400 hover:border-green-400"
                          }`}
                        >
                          {letter}
                        </button>
                        <input
                          type="text"
                          required
                          value={opt}
                          onChange={(e) => updateOption(qIdx, optIdx, e.target.value)}
                          placeholder={`Option ${letter}`}
                          className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                        />
                      </div>
                    );
                  })}
                  <p className="text-xs text-gray-400 mt-1">
                    Click the letter to mark the correct answer
                  </p>
                </div>
              ) : (
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    Expected Answer
                  </label>
                  <textarea
                    required
                    value={q.correct_answer}
                    onChange={(e) => updateQuestion(qIdx, "correct_answer", e.target.value)}
                    placeholder="Write the expected answer outline (50-200 words)..."
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                  />
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={addQuestion}
            className="flex items-center gap-1 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
          >
            <Plus size={16} /> Add Question
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm font-medium"
          >
            {loading ? "Saving..." : `Save Quiz (${questions.length} Q)`}
          </button>
        </div>
      </form>
    </div>
  );
}
