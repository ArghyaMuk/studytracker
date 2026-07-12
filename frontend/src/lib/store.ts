import { create } from "zustand";

interface User {
  id: number;
  name: string;
  email: string;
  college: string | null;
  university: string | null;
  program_id: number | null;
  current_semester: number | null;
  daily_study_hours_target: number | null;
  goal_type: string | null;
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  login: (user: User, accessToken: string, refreshToken: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated:
    typeof window !== "undefined" ? !!localStorage.getItem("access_token") : false,
  login: (user, accessToken, refreshToken) => {
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    set({ user, isAuthenticated: true });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ user: null, isAuthenticated: false });
  },
  setUser: (user) => set({ user }),
}));
