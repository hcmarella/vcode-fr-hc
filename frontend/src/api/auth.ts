import { apiClient } from "./client";
import type { Team, UserResponse } from "./types";

export const authApi = {
  me: () => apiClient.get<UserResponse>("/api/auth/me"),
  login: (email: string, password: string) =>
    apiClient.post<UserResponse>("/api/auth/login", { email, password }),
  signup: (email: string, password: string, name: string, team: Team) =>
    apiClient.post<UserResponse>("/api/auth/signup", { email, password, name, team }),
  logout: () => apiClient.post<void>("/api/auth/logout"),
};
