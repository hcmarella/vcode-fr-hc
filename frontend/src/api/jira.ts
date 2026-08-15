import { apiClient } from "./client";

export interface JiraIssue {
  key: string;
  summary: string;
  status: string;
  assignee: string | null;
  issuetype: string;
  priority: string | null;
  updated: string;
}

export interface JiraActionResponse {
  id: string;
  action_type: "create_issue" | "update_issue";
  preview_text: string;
  status: "pending" | "confirmed" | "rejected" | "executed" | "failed";
  created_at: string;
  result: Record<string, unknown> | null;
  error_message: string | null;
}

export const jiraApi = {
  search: (jql: string) => apiClient.get<JiraIssue[]>(`/api/jira/search?jql=${encodeURIComponent(jql)}`),
  actions: () => apiClient.get<JiraActionResponse[]>("/api/jira/actions"),
  confirm: (id: string) => apiClient.post<{ status: string }>(`/api/jira/actions/${id}/confirm`),
  reject: (id: string) => apiClient.post<{ status: string }>(`/api/jira/actions/${id}/reject`),
};
