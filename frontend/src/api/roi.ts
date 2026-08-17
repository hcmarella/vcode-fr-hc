import { apiClient } from "./client";

export interface RoiBreakdownItem {
  label: string;
  count: number;
  minutes_per_unit: number;
}

export interface RoiStatsResponse {
  breakdown: RoiBreakdownItem[];
  total_minutes_saved: number;
  total_hours_saved: number;
  hourly_rate_usd: number;
  total_value_usd: number;
}

export const roiApi = {
  stats: () => apiClient.get<RoiStatsResponse>("/api/roi/stats"),
};
