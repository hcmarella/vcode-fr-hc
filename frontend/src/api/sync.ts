import { apiClient } from "./client";
import type { SyncRunFlagResponse, SyncRunResponse } from "./types";

export const syncApi = {
  runs: () => apiClient.get<SyncRunResponse[]>("/api/sync/runs"),
  flags: () => apiClient.get<SyncRunFlagResponse[]>("/api/sync/flags"),
  trigger: (source: string, ref?: string) =>
    apiClient.post<SyncRunResponse>("/api/sync/run", { source, ref: ref ?? null }),
  // Unlike runs/flags above, /status is visible to any authenticated user
  // (not just admins) -- it's just "is content current," not sync internals.
  status: () => apiClient.get<SyncRunResponse | null>("/api/sync/status"),
};
