import { apiClient } from "./client";
import type { SyncRunFlagResponse, SyncRunResponse } from "./types";

export const syncApi = {
  runs: () => apiClient.get<SyncRunResponse[]>("/api/sync/runs"),
  flags: () => apiClient.get<SyncRunFlagResponse[]>("/api/sync/flags"),
  trigger: (source: string, ref?: string) =>
    apiClient.post<SyncRunResponse>("/api/sync/run", { source, ref: ref ?? null }),
};
