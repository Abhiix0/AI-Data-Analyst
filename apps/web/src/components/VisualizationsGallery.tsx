"use client";

import React from "react";
import { BarChart3, PieChart, Activity, Layers, Download } from "lucide-react";

interface VisualizationsGalleryProps {
  charts: any[];
  loading?: boolean;
}

export const VisualizationsGallery: React.FC<VisualizationsGalleryProps> = ({
  charts,
  loading,
}) => {
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-20 text-center text-slate-400 space-y-3">
        <Activity className="w-8 h-8 mx-auto animate-pulse text-accent-400" />
        <p>Loading interactive visualizations...</p>
      </div>
    );
  }

  if (!charts || charts.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-20 text-center space-y-3">
        <BarChart3 className="w-10 h-10 mx-auto text-slate-500" />
        <h3 className="text-lg font-bold text-white">No Visualizations Available</h3>
        <p className="text-slate-400 text-sm">
          Run an analysis or select a dataset with numeric columns to automatically generate chart distributions.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 space-y-8">
      <div>
        <h1 className="text-2xl font-black text-white">Interactive Visualizations</h1>
        <p className="text-sm text-slate-400">
          Autonomously selected chart projections, distribution histograms, and correlation matrices.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {charts.map((chart, i) => {
          const title = chart.title || `Visualization ${i + 1}`;
          const type = chart.chart_type || chart.type || "Chart";
          const desc = chart.description || "";
          const data = chart.data || [];

          return (
            <div key={i} className="glass-panel p-6 rounded-2xl space-y-4 border border-slate-800">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">{title}</h3>
                  <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-slate-800 text-accent-400">
                    {type}
                  </span>
                </div>
              </div>

              {desc && <p className="text-xs text-slate-400">{desc}</p>}

              {/* Chart Placeholder / Data Rendering */}
              <div className="h-56 rounded-xl bg-slate-950/80 border border-slate-800/80 p-4 flex flex-col justify-center items-center text-xs text-slate-400 font-mono overflow-auto">
                {data && data.length > 0 ? (
                  <div className="w-full space-y-2">
                    <p className="text-[11px] text-slate-500 uppercase font-semibold">Sample Data points ({data.length})</p>
                    <div className="max-h-36 overflow-y-auto space-y-1 text-slate-300">
                      {data.slice(0, 5).map((row: any, idx: number) => (
                        <div key={idx} className="p-1.5 rounded bg-slate-900 border border-slate-800/60 truncate">
                          {JSON.stringify(row)}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center space-y-2">
                    <PieChart className="w-8 h-8 mx-auto text-slate-600" />
                    <span>Plotly Interactive Chart Rendered</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
