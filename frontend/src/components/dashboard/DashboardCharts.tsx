"use client";

import type { ReactNode } from "react";
import type { ScoreBin } from "@/lib/types";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface DashboardChartsProps {
  packagesByYear: Record<string, number>;
  scoreDistribution: ScoreBin[];
}

function ChartCard({ title, description, children }: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <section className="glass-card rounded-2xl p-6" aria-labelledby={title.toLowerCase().replaceAll(" ", "-")}>
      <div className="mb-4">
        <h2 id={title.toLowerCase().replaceAll(" ", "-")} className="text-lg font-semibold text-surface-900 dark:text-white">
          {title}
        </h2>
        <p className="text-sm text-surface-500 dark:text-surface-400">{description}</p>
      </div>
      {children}
    </section>
  );
}

const tooltipStyle = {
  backgroundColor: "#1e293b",
  border: "1px solid #334155",
  borderRadius: "12px",
  color: "#e2e8f0",
};

export function DashboardCharts({ packagesByYear, scoreDistribution }: DashboardChartsProps) {
  const yearRows = Object.entries(packagesByYear).map(([year, count]) => ({ year, count }));
  const scoreRows = scoreDistribution.map((bin) => ({ range: bin.range_label, count: bin.count }));

  return (
    <div className="grid grid-cols-1 gap-6 mb-8">
      <ChartCard
        title="Distribusi Paket per Tahun"
        description="Jumlah paket eligible per tahun. Tahun 2026 ditandai sebagai snapshot parsial, bukan tahun penuh."
      >
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={yearRows} margin={{ top: 8, right: 12, left: 0, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
            <XAxis dataKey="year" tick={{ fill: "#64748b", fontSize: 12 }} />
            <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} />
            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#f8fafc" }} />
            <Bar dataKey="count" name="Paket" fill="#4f46e5" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>

      <ChartCard
        title="Distribusi Skor Anomali"
        description="Sebaran skor model untuk memahami rentang prioritas pemeriksaan. Skor bukan label fraud."
      >
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={scoreRows} margin={{ top: 8, right: 12, left: 0, bottom: 48 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.25} />
            <XAxis
              dataKey="range"
              angle={-35}
              textAnchor="end"
              interval={0}
              tick={{ fill: "#64748b", fontSize: 11 }}
            />
            <YAxis allowDecimals={false} tick={{ fill: "#64748b", fontSize: 12 }} />
            <Tooltip contentStyle={tooltipStyle} labelStyle={{ color: "#f8fafc" }} />
            <Bar dataKey="count" name="Jumlah Paket" fill="#06b6d4" radius={[8, 8, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}
