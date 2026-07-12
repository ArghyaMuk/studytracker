import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE}/api/v1`,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 - try refresh
api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const orig = error.config;
    if (error.response?.status === 401 && !orig._retry) {
      orig._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");
      if (refreshToken) {
        try {
          const { data } = await axios.post(`${API_BASE}/api/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          localStorage.setItem("access_token", data.access_token);
          localStorage.setItem("refresh_token", data.refresh_token);
          orig.headers.Authorization = `Bearer ${data.access_token}`;
          return api(orig);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;

// Auth
export const authApi = {
  register: (data: {
    name: string;
    email: string;
    password: string;
    college?: string;
    university?: string;
    current_semester?: number;
  }) => api.post("/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/auth/login", data),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
};

// Users
export const userApi = {
  getProfile: (userId: number) => api.get(`/users/${userId}`),
  updateProfile: (userId: number, data: Record<string, unknown>) =>
    api.put(`/users/${userId}`, data),
  setExamTarget: (
    userId: number,
    data: { subject_code: string; exam_type: string; exam_date: string }
  ) => api.put(`/users/${userId}/exam-targets`, data),
};

// Curriculum
export const curriculumApi = {
  getPrograms: () => api.get("/programs"),
  getSubjects: (programId: number, semester: number) =>
    api.get(`/programs/${programId}/semesters/${semester}/subjects`),
  getUnits: (subjectCode: string) => api.get(`/subjects/${subjectCode}/units`),
};

// Sessions
export const sessionApi = {
  create: (
    userId: number,
    data: {
      subject_code: string;
      unit_number: number;
      duration_min: number;
      focus_rating: number;
      notes?: string;
    }
  ) => api.post(`/sessions?user_id=${userId}`, data),
  list: (userId: number, subjectCode?: string) =>
    api.get("/sessions", { params: { user_id: userId, subject_code: subjectCode } }),
  delete: (sessionId: number) => api.delete(`/sessions/${sessionId}`),
};

// Quizzes
export const quizApi = {
  generate: (
    userId: number,
    data: {
      subject_code: string;
      unit_number?: number;
      difficulty?: string;
      count?: number;
      mode?: string;
    }
  ) => api.post(`/quizzes/generate?user_id=${userId}`, data),
  get: (quizId: number) => api.get(`/quizzes/${quizId}`),
  submit: (quizId: number, userId: number, answers: Record<number, string>) =>
    api.post(`/quizzes/${quizId}/submit?user_id=${userId}`, { answers }),
};

// Revision
export const revisionApi = {
  getToday: (userId: number) => api.get(`/revision/today?user_id=${userId}`),
  getUpcoming: (userId: number, days = 7) =>
    api.get(`/revision/upcoming?user_id=${userId}&days=${days}`),
  grade: (itemId: number, quality: number) =>
    api.post(`/revision/${itemId}/grade`, { quality }),
};

// Readiness
export const readinessApi = {
  getAll: (userId: number) => api.get(`/readiness/${userId}`),
  getSubject: (userId: number, subjectCode: string) =>
    api.get(`/readiness/${userId}/${subjectCode}`),
};

// Notifications
export const notificationApi = {
  getPreferences: (userId: number) =>
    api.get(`/notifications/preferences?user_id=${userId}`),
  updatePreferences: (userId: number, data: Record<string, unknown>) =>
    api.put(`/notifications/preferences?user_id=${userId}`, data),
};
