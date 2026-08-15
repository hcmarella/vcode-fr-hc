import { apiClient } from "./client";
import type { AboutResponse, AgentResponse, CommandResponse, KnowledgeResponse, SkillResponse } from "./types";

export const personasApi = {
  list: () => apiClient.get<AgentResponse[]>("/api/personas"),
  get: (slug: string) => apiClient.get<AgentResponse>(`/api/personas/${slug}`),
};

export const skillsApi = {
  list: () => apiClient.get<SkillResponse[]>("/api/skills"),
  get: (slug: string) => apiClient.get<SkillResponse>(`/api/skills/${slug}`),
};

export const commandsApi = {
  list: () => apiClient.get<CommandResponse[]>("/api/commands"),
  get: (slug: string) => apiClient.get<CommandResponse>(`/api/commands/${slug}`),
};

export const knowledgeApi = {
  list: () => apiClient.get<KnowledgeResponse[]>("/api/knowledge"),
  get: (id: string) => apiClient.get<KnowledgeResponse>(`/api/knowledge/${id}`),
};

export const aboutApi = {
  get: () => apiClient.get<AboutResponse>("/api/about"),
};
