import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, XAxis, YAxis } from "recharts";

import { CATEGORICAL, INK } from "./palette";

interface CategoryBarChartProps {
  data: { label: string; value: number }[];
  yAxisWidth?: number;
}

// Magnitude comparison across a handful of named categories -> horizontal
// bar, each bar its own categorical slot (axis labels already carry
// identity, so no separate legend box). Aqua/yellow slots (3, 4) sit under
// 3:1 contrast on this light surface -- the validator's relief rule -- so
// every bar gets a direct value label rather than relying on the fill alone.
// Shared by the Home dashboard's content-mix chart and the Knowledge page's
// type breakdown -- same shape, different data.
export default function CategoryBarChart({ data, yAxisWidth = 90 }: CategoryBarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={Math.max(120, data.length * 40)}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 28, bottom: 4, left: 8 }}
        barSize={20}
      >
        <CartesianGrid horizontal={false} stroke={INK.gridline} strokeDasharray="0" />
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="label"
          width={yAxisWidth}
          axisLine={{ stroke: INK.baseline }}
          tickLine={false}
          tick={{ fill: INK.secondary, fontSize: 12 }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {data.map((entry, i) => (
            <Cell key={entry.label} fill={CATEGORICAL[i % CATEGORICAL.length]} />
          ))}
          <LabelList dataKey="value" position="right" fill={INK.primary} fontSize={12} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
