import { apiClient } from "./client";

export interface ChatResponse {
  reply: string;
}

export const chatApi = {
  ask: (message: string) => apiClient.post<ChatResponse>("/api/chat", { message }),
};
