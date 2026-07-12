"use client";

import { useState } from "react";
import { Brain, CheckCircle, XCircle, Sparkles, PenLine, Plus, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import { useAuthStore } from "@/lib/store";
import { quizApi } from "@/lib/api";
import api from "@/lib/api";

interface Question {
  id: number;
  question: string;
  options_json: string | null;
  difficulty: string;
}

interface QuizResult {
  quiz_id: number;
  score: number;
  total_questions: number;
  correct_count: number;
  feedback: { question_id: number; correct: boolean; correct_answer: string; your_answer: string }[];
}

interface ManualQuestion {
  question: string;
  options: string[];
  correct_answer: string;
  difficulty: string;
}

export default function QuizzesPage() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.email === "admin@studypilot.com";
  const [step, setStep] = useState<"config" | "quiz" | "results">("config");
  const [tab, setTab] = useState<"ai" | "manual">("ai");
  const [config, setConfig] = useState({
    subject_code: "",
    unit_number: 1,
    difficulty: "medium",
    count: 5,
    mode: "mcq",
  });
  const [questions, setQuestions] = useState<Question[]>([]);
  const [quizId, setQuizId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Manual questions state
  const [manualQuestions, setManualQuestions] = useState<ManualQuestion[]>([
    { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
  ]);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;
    setLoading(true);
    try {
      const { data: quiz } = await quizApi.generate(user.id, config);
      setQuizId(quiz.id);
      const { data: fullQuiz } = await quizApi.get(quiz.id);
      setQuestions(fullQuiz.questions || []);
      setAnswers({});
      setStep("quiz");
      toast.success("Quiz generated!");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to generate quiz";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) return;

    const emptyQ = manualQuestions.find((q) => !q.question.trim());
    if (emptyQ) {
      toast.error("All questions must have text");
      return;
    }
    const emptyOpt = manualQuestions.find((q) => q.options.some((o) => !o.trim()));
    if (config.mode === "mcq" && emptyOpt) {
      toast.error("All options must be filled");
      return;
    }

    setLoading(true);
    try {
      const questionsPayload = manualQuestions.map((q) => ({
        question: q.question,
        options_json: config.mode === "mcq" ? JSON.stringify(q.options) : null,
        correct_answer: q.correct_answer,
        difficulty: q.difficulty,
      }));

      const { data } = await api.post(`/admin/quizzes/custom`, {
        subject_code: config.subject_code || "CUSTOM",
        unit_number: config.unit_number,
        mode: config.mode,
        questions: questionsPayload,
      });

      // Now fetch and take the quiz
      const { data: fullQuiz } = await quizApi.get(data.id);
      setQuizId(data.id);
      setQuestions(fullQuiz.questions || []);
      setAnswers({});
      setStep("quiz");
      toast.success("Quiz created! Start answering.");
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create quiz";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitQuiz = async () => {
    if (!user || !quizId) return;
    setLoading(true);
    try {
      const { data } = await quizApi.submit(quizId, user.id, answers);
      setResult(data);
      setStep("results");
    } catch {
      toast.error("Failed to submit quiz");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setStep("config");
    setQuestions([]);
    setAnswers({});
    setResult(null);
    setQuizId(null);
    setManualQuestions([
      { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
    ]);
  };

  const addManualQuestion = () => {
    setManualQuestions([
      ...manualQuestions,
      { question: "", options: ["", "", "", ""], correct_answer: "A", difficulty: "medium" },
    ]);
  };

  const removeManualQuestion = (index: number) => {
    if (manualQuestions.length <= 1) return;
    setManualQuestions(manualQuestions.filter((_, i) => i !== index));
  };

  const updateManualQuestion = (index: number, field: string, value: string) => {
    const updated = [...manualQuestions];
    updated[index] = { ...updated[index], [field]: value };
    setManualQuestions(updated);
  };

  const updateManualOption = (qIndex: number, optIndex: number, value: string) => {
    const updated = [...manualQuestions];
    updated[qIndex].options[optIndex] = value;
    setManualQuestions(updated);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Quizzes</h1>
        <p className="text-gray-500 mt-1">Generate from AI or create your own practice quizzes</p>
      </div>

      {step === "config" && (
        <div className="max-w-2xl">
          {/* Tabs */}
          <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
            <button
              onClick={() => setTab("ai")}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                tab === "ai"
                  ? "bg-white text-indigo-700 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              <Sparkles size={16} /> AI Generate
            </button>
            {isAdmin && (
              <button
                onClick={() => setTab("manual")}
                className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  tab === "manual"
                    ? "bg-white text-indigo-700 shadow-sm"
                    : "text-gray-600 hover:text-gray-900"
                }`}
              >
                <PenLine size={16} /> Manual Add
              </button>
            )}
          </div>

          {/* AI Generate Tab */}
          {tab === "ai" && (
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Generate a Quiz with AI</h2>
              <form onSubmit={handleGenerate} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Subject Code</label>
                  <input
                    type="text"
                    required
                    value={config.subject_code}
                    onChange={(e) => setConfig({ ...config, subject_code: e.target.value })}
                    placeholder="e.g. CS301"
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unit Number</label>
                    <input
                      type="number"
                      min={1}
                      value={config.unit_number}
                      onChange={(e) => setConfig({ ...config, unit_number: parseInt(e.target.value) })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Questions</label>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={config.count}
                      onChange={(e) => setConfig({ ...config, count: parseInt(e.target.value) })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
                    <select
                      value={config.difficulty}
                      onChange={(e) => setConfig({ ...config, difficulty: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    >
                      <option value="easy">Easy</option>
                      <option value="medium">Medium</option>
                      <option value="hard">Hard</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Mode</label>
                    <select
                      value={config.mode}
                      onChange={(e) => setConfig({ ...config, mode: e.target.value })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    >
                      <option value="mcq">MCQ</option>
                      <option value="viva">Viva Q&A</option>
                    </select>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Sparkles size={16} />
                  {loading ? "Generating..." : "Generate Quiz"}
                </button>
              </form>
            </div>
          )}

          {/* Manual Add Tab */}
          {tab === "manual" && (
            <div className="space-y-4">
              <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Your Own Quiz</h2>
                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Subject Code (optional)</label>
                    <input
                      type="text"
                      value={config.subject_code}
                      onChange={(e) => setConfig({ ...config, subject_code: e.target.value })}
                      placeholder="e.g. CS301"
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Unit Number</label>
                    <input
                      type="number"
                      min={1}
                      value={config.unit_number}
                      onChange={(e) => setConfig({ ...config, unit_number: parseInt(e.target.value) })}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-gray-900"
                    />
                  </div>
                </div>
              </div>

              <form onSubmit={handleManualSubmit} className="space-y-4">
                {manualQuestions.map((q, qIdx) => (
                  <div key={qIdx} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-semibold text-gray-700">Question {qIdx + 1}</h3>
                      <div className="flex items-center gap-2">
                        <select
                          value={q.difficulty}
                          onChange={(e) => updateManualQuestion(qIdx, "difficulty", e.target.value)}
                          className="text-xs px-2 py-1 border border-gray-200 rounded text-gray-600"
                        >
                          <option value="easy">Easy</option>
                          <option value="medium">Medium</option>
                          <option value="hard">Hard</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => removeManualQuestion(qIdx)}
                          className="p-1 text-red-400 hover:text-red-600"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    <textarea
                      required
                      value={q.question}
                      onChange={(e) => updateManualQuestion(qIdx, "question", e.target.value)}
                      placeholder="Type your question here..."
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 mb-3"
                    />
                    <div className="space-y-2">
                      {q.options.map((opt, optIdx) => {
                        const letter = String.fromCharCode(65 + optIdx);
                        const isCorrect = q.correct_answer === letter;
                        return (
                          <div key={optIdx} className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => updateManualQuestion(qIdx, "correct_answer", letter)}
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
                              onChange={(e) => updateManualOption(qIdx, optIdx, e.target.value)}
                              placeholder={`Option ${letter}`}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                            />
                          </div>
                        );
                      })}
                      <p className="text-xs text-gray-400">Click the letter to mark the correct answer</p>
                    </div>
                  </div>
                ))}

                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={addManualQuestion}
                    className="flex items-center gap-1 px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm"
                  >
                    <Plus size={16} /> Add Question
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm font-medium flex items-center gap-2"
                  >
                    <PenLine size={16} />
                    {loading ? "Creating..." : `Start Quiz (${manualQuestions.length} Q)`}
                  </button>
                </div>
              </form>
            </div>
          )}
        </div>
      )}

      {step === "quiz" && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">
              Quiz — {config.subject_code || "Custom"} Unit {config.unit_number}
            </h2>
            <span className="text-sm text-gray-500">
              {Object.keys(answers).length}/{questions.length} answered
            </span>
          </div>
          {questions.map((q, idx) => {
            const options: string[] = q.options_json ? JSON.parse(q.options_json) : [];
            return (
              <div key={q.id} className="bg-white rounded-xl p-5 shadow-sm border border-gray-100">
                <p className="font-medium text-gray-900 mb-3">
                  {idx + 1}. {q.question}
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {options.map((opt, i) => {
                    const letter = String.fromCharCode(65 + i);
                    const selected = answers[q.id] === letter;
                    return (
                      <button
                        key={i}
                        onClick={() => setAnswers({ ...answers, [q.id]: letter })}
                        className={`p-3 text-left rounded-lg border text-sm transition-colors ${
                          selected
                            ? "border-indigo-500 bg-indigo-50 text-indigo-700"
                            : "border-gray-200 hover:border-indigo-300 text-gray-700"
                        }`}
                      >
                        <span className="font-medium">{letter}.</span> {opt}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
          <button
            onClick={handleSubmitQuiz}
            disabled={loading || Object.keys(answers).length === 0}
            className="px-6 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "Submitting..." : "Submit Quiz"}
          </button>
        </div>
      )}

      {step === "results" && result && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center">
            <Brain size={40} className="mx-auto text-indigo-600 mb-3" />
            <h2 className="text-2xl font-bold text-gray-900">{result.score.toFixed(0)}%</h2>
            <p className="text-gray-500 mt-1">
              {result.correct_count}/{result.total_questions} correct
            </p>
          </div>

          <div className="space-y-3">
            {result.feedback.map((fb, idx) => (
              <div
                key={fb.question_id}
                className={`p-4 rounded-lg border ${
                  fb.correct ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
                }`}
              >
                <div className="flex items-center gap-2">
                  {fb.correct ? (
                    <CheckCircle size={18} className="text-green-600" />
                  ) : (
                    <XCircle size={18} className="text-red-600" />
                  )}
                  <span className="text-sm font-medium text-gray-700">
                    Question {idx + 1}:{" "}
                    {fb.correct ? "Correct" : `Wrong (correct: ${fb.correct_answer})`}
                  </span>
                </div>
              </div>
            ))}
          </div>

          <button
            onClick={reset}
            className="px-6 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Take Another Quiz
          </button>
        </div>
      )}
    </div>
  );
}
