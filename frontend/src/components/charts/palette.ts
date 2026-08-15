// Validated categorical palette (dataviz skill's reference instance), light
// mode only -- this app has no dark-mode toggle anywhere else, so a
// dark-mode chart variant would be inconsistent with everything around it.
// Order is fixed and load-bearing for CVD safety; never reassign per-chart.
export const CATEGORICAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"] as const;

export const STATUS = {
  good: "#0ca30c",
  warning: "#fab219",
  serious: "#ec835a",
  critical: "#d03b3b",
} as const;

export const INK = {
  primary: "#0b0b0b",
  secondary: "#52514e",
  muted: "#898781",
  gridline: "#e1e0d9",
  baseline: "#c3c2b7",
};
