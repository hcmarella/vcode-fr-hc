import { apiClient } from "./client";

export interface GitHubContributor {
  login: string;
  pr_count: number;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: "open" | "closed" | "merged";
  author: string | null;
  created_at: string;
  merged_at: string | null;
  html_url: string;
  synthetic: boolean;
}

export interface GitHubRepoStats {
  repo: string;
  open_count: number;
  merged_count: number;
  closed_unmerged_count: number;
  stale_open_count: number;
  avg_merge_hours: number | null;
  top_contributors: GitHubContributor[];
  recent_prs: GitHubPullRequest[];
  demo_data_included: boolean;
}

export interface GitHubStatsResponse {
  repos: GitHubRepoStats[];
  totals: {
    open_count: number;
    merged_count: number;
    closed_unmerged_count: number;
    stale_open_count: number;
    demo_data_included: boolean;
  };
}

export const githubApi = {
  stats: () => apiClient.get<GitHubStatsResponse>("/api/github/stats"),
};
