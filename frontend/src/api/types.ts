export type Team = "engineering" | "product" | "qa" | "docs";
export type Role = "member" | "admin";
export type ContentStatus = "active" | "stale";
export type MemoryType = "user" | "feedback" | "project" | "reference";
export type SyncRunStatus = "running" | "success" | "failed";
export type SyncFlagType = "team_mismatch" | "parse_error" | "other";
export type SyncContentType = "agent" | "skill" | "command" | "knowledge" | "about";

export interface UserResponse {
  id: string;
  email: string;
  name: string;
  team: Team;
  role: Role;
}

export interface AgentResponse {
  id: string;
  name: string;
  slug: string;
  description: string;
  tools: string[];
  model: string;
  body_markdown: string;
  status: ContentStatus;
  updated_at: string;
}

export interface SkillResponse {
  id: string;
  name: string;
  slug: string;
  description: string;
  body_markdown: string;
  status: ContentStatus;
  updated_at: string;
}

export interface CommandResponse {
  id: string;
  slug: string;
  description: string;
  argument_hint: string | null;
  body_markdown: string;
  status: ContentStatus;
  updated_at: string;
}

export interface KnowledgeResponse {
  id: string;
  name: string;
  description: string;
  metadata_type: MemoryType;
  effective_team: Team;
  team_mismatch: boolean;
  body_markdown: string;
  status: ContentStatus;
  updated_at: string;
}

export interface AboutResponse {
  body_markdown: string;
  updated_at: string;
}

export interface SyncRunResponse {
  id: string;
  started_at: string;
  finished_at: string | null;
  status: SyncRunStatus;
  source_ref: string;
  source_commit_sha: string | null;
  counts_json: Record<string, Record<string, number>>;
  error_message: string | null;
}

export interface SyncRunFlagResponse {
  id: string;
  sync_run_id: string;
  flag_type: SyncFlagType;
  source_path: string;
  content_type: SyncContentType;
  details_json: Record<string, unknown>;
  created_at: string;
}
