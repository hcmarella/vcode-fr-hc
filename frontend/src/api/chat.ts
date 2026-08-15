import { apiClient } from "./client";

export interface ProposedAction {
  id: string;
  action_type: "create_issue" | "update_issue";
  preview_text: string;
}

export interface ChatResponse {
  reply: string;
  // Non-empty only when the model staged a Jira create/update this turn --
  // nothing in these has been written to Jira. Render as Confirm/Reject.
  proposed_actions: ProposedAction[];
}

export const chatApi = {
  ask: (message: string) => apiClient.post<ChatResponse>("/api/chat", { message }),
};
