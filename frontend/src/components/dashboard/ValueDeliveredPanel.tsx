import { useQuery } from "@tanstack/react-query";

import { roiApi } from "../../api/roi";

const currency = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

export default function ValueDeliveredPanel() {
  const query = useQuery({ queryKey: ["roi", "stats"], queryFn: roiApi.stats });

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-sm font-medium text-slate-900">Value delivered</h2>
        <span className="shrink-0 rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-medium text-amber-800">
          Illustrative estimate
        </span>
      </div>

      {query.isLoading && (
        <div className="mt-3 h-24 animate-pulse rounded-lg bg-slate-50" />
      )}

      {query.data && (
        <>
          <div className="mt-3 flex items-baseline gap-3">
            <p className="text-3xl font-semibold tabular-nums text-slate-900">
              {query.data.total_hours_saved.toLocaleString()}
              <span className="ml-1 text-base font-medium text-slate-500">hrs saved</span>
            </p>
            <p className="text-lg font-medium tabular-nums text-emerald-700">
              ≈ {currency.format(query.data.total_value_usd)}
            </p>
          </div>

          <ul className="mt-4 space-y-1.5">
            {query.data.breakdown.map((item) => (
              <li key={item.label} className="flex items-center justify-between text-xs">
                <span className="text-slate-600">{item.label}</span>
                <span className="tabular-nums text-slate-500">
                  {item.count} × {item.minutes_per_unit} min
                </span>
              </li>
            ))}
          </ul>

          <p className="mt-4 border-t border-slate-100 pt-3 text-[11px] leading-relaxed text-slate-400">
            Based on {query.data.breakdown.reduce((sum, i) => sum + i.count, 0)} portal-assisted
            tasks (tickets drafted, docs/PR sessions, syncs) at the per-task minute estimates
            above and a blended rate of {currency.format(query.data.hourly_rate_usd)}/hr — not a
            measured time-tracking figure.
          </p>
        </>
      )}
    </div>
  );
}
