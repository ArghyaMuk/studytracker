"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Plus, Trash2, BookOpen, GraduationCap, ClipboardList } from "lucide-react";
import toast from "react-hot-toast";
import { curriculumApi } from "@/lib/api";
import api from "@/lib/api";
import { useAuthStore } from "@/lib/store";

interface Program {
  id: number;
  name: string;
  total_semesters: number;
}

interface Subject {
  id: number;
  code: string;
  name: string;
  semester: number;
  type: string;
  credits: number;
  units: { id: number; unit_number: number; unit_title: string; topics_json: string | null }[];
}

interface UnitInput {
  unit_number: number;
  unit_title: string;
  topics_json: string;
}

export default function AdminPage() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [selectedProgram, setSelectedProgram] = useState<Program | null>(null);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [selectedSemester, setSelectedSemester] = useState(1);

  // Program form
  const [showProgramForm, setShowProgramForm] = useState(false);
  const [programForm, setProgramForm] = useState({ name: "", total_semesters: 8 });

  // Subject form
  const [showSubjectForm, setShowSubjectForm] = useState(false);
  const [subjectForm, setSubjectForm] = useState({
    code: "",
    name: "",
    semester: 1,
    type: "theory" as "theory" | "lab",
    credits: 3,
  });
  const [units, setUnits] = useState<UnitInput[]>([
    { unit_number: 1, unit_title: "", topics_json: "" },
  ]);

  const [loading, setLoading] = useState(false);

  const handleDeleteProgram = async (prog: Program) => {
    if (!confirm(`Delete "${prog.name}" and all its subjects? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/programs/${prog.id}`);
      setPrograms(programs.filter((p) => p.id !== prog.id));
      if (selectedProgram?.id === prog.id) {
        setSelectedProgram(null);
        setSubjects([]);
      }
      toast.success(`Program "${prog.name}" deleted`);
    } catch {
      toast.error("Failed to delete program");
    }
  };

  const handleDeleteSubject = async (subject: Subject) => {
    if (!confirm(`Delete subject "${subject.code} - ${subject.name}"? This cannot be undone.`)) return;
    try {
      await api.delete(`/admin/subjects/${subject.id}`);
      setSubjects(subjects.filter((s) => s.id !== subject.id));
      toast.success(`Subject "${subject.code}" deleted`);
    } catch {
      toast.error("Failed to delete subject");
    }
  };

  // Load programs
  useEffect(() => {
    curriculumApi.getPrograms().then(({ data }) => setPrograms(data)).catch(() => {});
  }, []);

  // Load subjects when program/semester changes
  useEffect(() => {
    if (!selectedProgram) {
      setSubjects([]);
      return;
    }
    curriculumApi
      .getSubjects(selectedProgram.id, selectedSemester)
      .then(({ data }) => setSubjects(data))
      .catch(() => setSubjects([]));
  }, [selectedProgram, selectedSemester]);

  const handleCreateProgram = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const { data } = await api.post("/admin/programs", programForm);
      setPrograms([...programs, data]);
      setShowProgramForm(false);
      setProgramForm({ name: "", total_semesters: 8 });
      toast.success(`Program "${data.name}" created!`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create program";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProgram) return;
    setLoading(true);
    try {
      const payload = {
        ...subjectForm,
        semester: selectedSemester,
        units: units.filter((u) => u.unit_title.trim() !== ""),
      };
      const { data } = await api.post(
        `/admin/programs/${selectedProgram.id}/subjects`,
        payload
      );
      setSubjects([...subjects, data]);
      setShowSubjectForm(false);
      setSubjectForm({ code: "", name: "", semester: 1, type: "theory", credits: 3 });
      setUnits([{ unit_number: 1, unit_title: "", topics_json: "" }]);
      toast.success(`Subject "${data.name}" added!`);
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create subject";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const addUnit = () => {
    setUnits([...units, { unit_number: units.length + 1, unit_title: "", topics_json: "" }]);
  };

  const removeUnit = (index: number) => {
    if (units.length <= 1) return;
    const updated = units.filter((_, i) => i !== index).map((u, i) => ({ ...u, unit_number: i + 1 }));
    setUnits(updated);
  };

  const updateUnit = (index: number, field: keyof UnitInput, value: string | number) => {
    const updated = [...units];
    updated[index] = { ...updated[index], [field]: value };
    setUnits(updated);
  };

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Course Administration</h1>
        <p className="text-gray-500 mt-1">Add programs, subjects, and units to the curriculum</p>
        <Link
          href="/admin/quizzes"
          className="inline-flex items-center gap-2 mt-3 px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
        >
          <ClipboardList size={16} /> Create Custom Quiz
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Programs Panel */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="font-semibold text-gray-900 flex items-center gap-2">
                <GraduationCap size={18} /> Programs
              </h2>
              <button
                onClick={() => setShowProgramForm(!showProgramForm)}
                className="p-1.5 text-indigo-600 hover:bg-indigo-50 rounded-lg"
              >
                <Plus size={18} />
              </button>
            </div>

            {showProgramForm && (
              <form onSubmit={handleCreateProgram} className="p-4 border-b border-gray-100 bg-gray-50">
                <input
                  type="text"
                  required
                  value={programForm.name}
                  onChange={(e) => setProgramForm({ ...programForm, name: e.target.value })}
                  placeholder="Program name (e.g. B.Tech CSE)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 mb-2"
                />
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={1}
                    max={12}
                    value={programForm.total_semesters}
                    onChange={(e) =>
                      setProgramForm({ ...programForm, total_semesters: parseInt(e.target.value) })
                    }
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                  />
                  <span className="text-xs text-gray-500 self-center">semesters</span>
                  <button
                    type="submit"
                    disabled={loading}
                    className="ml-auto px-3 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Add
                  </button>
                </div>
              </form>
            )}

            <div className="divide-y divide-gray-100 max-h-96 overflow-y-auto">
              {programs.length === 0 ? (
                <p className="p-4 text-sm text-gray-400 text-center">No programs yet</p>
              ) : (
                programs.map((prog) => (
                  <div
                    key={prog.id}
                    className={`flex items-center justify-between p-4 hover:bg-gray-50 transition-colors ${
                      selectedProgram?.id === prog.id ? "bg-indigo-50 border-l-2 border-indigo-500" : ""
                    }`}
                  >
                    <button
                      onClick={() => {
                        setSelectedProgram(prog);
                        setSelectedSemester(1);
                      }}
                      className="flex-1 text-left"
                    >
                      <div className="font-medium text-sm text-gray-900">{prog.name}</div>
                      <div className="text-xs text-gray-500">{prog.total_semesters} semesters</div>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteProgram(prog);
                      }}
                      className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                      title="Delete program"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Subjects Panel */}
        <div className="lg:col-span-2">
          {!selectedProgram ? (
            <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
              <GraduationCap size={40} className="mx-auto text-gray-300 mb-3" />
              <p className="text-gray-500">Select a program to view and add subjects</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Semester selector */}
              <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 flex items-center gap-4">
                <span className="text-sm font-medium text-gray-700">
                  {selectedProgram.name} →
                </span>
                <div className="flex gap-1 flex-wrap">
                  {Array.from({ length: selectedProgram.total_semesters }, (_, i) => i + 1).map(
                    (sem) => (
                      <button
                        key={sem}
                        onClick={() => setSelectedSemester(sem)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                          selectedSemester === sem
                            ? "bg-indigo-600 text-white"
                            : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                        }`}
                      >
                        Sem {sem}
                      </button>
                    )
                  )}
                </div>
                <button
                  onClick={() => setShowSubjectForm(!showSubjectForm)}
                  className="ml-auto flex items-center gap-1 px-3 py-1.5 bg-indigo-600 text-white text-xs font-medium rounded-lg hover:bg-indigo-700"
                >
                  <Plus size={14} /> Add Subject
                </button>
              </div>

              {/* Add Subject Form */}
              {showSubjectForm && (
                <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
                  <h3 className="font-semibold text-gray-900 mb-4">
                    Add Subject to Semester {selectedSemester}
                  </h3>
                  <form onSubmit={handleCreateSubject} className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Subject Code
                        </label>
                        <input
                          type="text"
                          required
                          value={subjectForm.code}
                          onChange={(e) => setSubjectForm({ ...subjectForm, code: e.target.value })}
                          placeholder="e.g. CS301"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-600 mb-1">
                          Subject Name
                        </label>
                        <input
                          type="text"
                          required
                          value={subjectForm.name}
                          onChange={(e) => setSubjectForm({ ...subjectForm, name: e.target.value })}
                          placeholder="e.g. Data Structures"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                        />
                      </div>
                      <div className="flex gap-2">
                        <div className="flex-1">
                          <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                          <select
                            value={subjectForm.type}
                            onChange={(e) =>
                              setSubjectForm({
                                ...subjectForm,
                                type: e.target.value as "theory" | "lab",
                              })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                          >
                            <option value="theory">Theory</option>
                            <option value="lab">Lab</option>
                          </select>
                        </div>
                        <div className="w-20">
                          <label className="block text-xs font-medium text-gray-600 mb-1">Credits</label>
                          <input
                            type="number"
                            min={1}
                            max={10}
                            value={subjectForm.credits}
                            onChange={(e) =>
                              setSubjectForm({ ...subjectForm, credits: parseInt(e.target.value) })
                            }
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                          />
                        </div>
                      </div>
                    </div>

                    {/* Units */}
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <label className="text-xs font-medium text-gray-600">
                          Units / Modules
                        </label>
                        <button
                          type="button"
                          onClick={addUnit}
                          className="text-xs text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                        >
                          <Plus size={12} /> Add Unit
                        </button>
                      </div>
                      <div className="space-y-2">
                        {units.map((unit, idx) => (
                          <div key={idx} className="flex gap-2 items-start">
                            <span className="text-xs text-gray-400 mt-2.5 w-6 shrink-0">
                              {unit.unit_number}.
                            </span>
                            <input
                              type="text"
                              required
                              value={unit.unit_title}
                              onChange={(e) => updateUnit(idx, "unit_title", e.target.value)}
                              placeholder="Unit title"
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                            />
                            <input
                              type="text"
                              value={unit.topics_json}
                              onChange={(e) => updateUnit(idx, "topics_json", e.target.value)}
                              placeholder='Topics (e.g. ["arrays","trees"])'
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900"
                            />
                            <button
                              type="button"
                              onClick={() => removeUnit(idx)}
                              className="p-2 text-red-400 hover:text-red-600 mt-0.5"
                            >
                              <Trash2 size={14} />
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <button
                        type="submit"
                        disabled={loading}
                        className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {loading ? "Saving..." : "Create Subject"}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowSubjectForm(false)}
                        className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                </div>
              )}

              {/* Subjects List */}
              {subjects.length === 0 && !showSubjectForm ? (
                <div className="bg-white rounded-xl p-8 shadow-sm border border-gray-100 text-center">
                  <BookOpen size={32} className="mx-auto text-gray-300 mb-2" />
                  <p className="text-gray-500 text-sm">
                    No subjects in Semester {selectedSemester}. Add one above.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {subjects.map((subject) => (
                    <div
                      key={subject.id}
                      className="bg-white rounded-xl p-5 shadow-sm border border-gray-100"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 text-xs font-mono rounded">
                            {subject.code}
                          </span>
                          <h3 className="font-medium text-gray-900">{subject.name}</h3>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            subject.type === "theory"
                              ? "bg-blue-50 text-blue-600"
                              : "bg-green-50 text-green-600"
                          }`}>
                            {subject.type}
                          </span>
                          <span className="text-xs text-gray-400">{subject.credits} cr</span>
                          <button
                            onClick={() => handleDeleteSubject(subject)}
                            className="p-1.5 text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg"
                            title="Delete subject"
                          >
                            <Trash2 size={14} />
                          </button>
                        </div>
                      </div>
                      {subject.units && subject.units.length > 0 && (
                        <div className="mt-3 pl-3 border-l-2 border-gray-100 space-y-1">
                          {subject.units.map((unit) => (
                            <div key={unit.id} className="text-sm text-gray-600">
                              <span className="text-gray-400">Unit {unit.unit_number}:</span>{" "}
                              {unit.unit_title}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
