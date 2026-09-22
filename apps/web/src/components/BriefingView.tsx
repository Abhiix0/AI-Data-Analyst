"use client";

import React from "react";
import { Activity, AlertTriangle, CheckCircle, Database, Layers, Sparkles } from "lucide-react";
import { DatasetBriefing, FindingItem } from "@/lib/api";
import { FindingCard } from "@/components/FindingCard";

interface BriefingViewProps {
  briefing: DatasetBriefing | null;
  loading: boolean;
  onDrillDown: (res: any) => void;
  onRefreshBriefing?: () => void;
}

export const BriefingView: React.FC<BriefingViewProps> = ({
  briefing,
  loading,
  onDrillDown,
}) => {
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto py-20 text-center space-y-4">
        <div className="inline-block p-4 rounded-2xl bg-brand-500/10 text-brand-400 animate-pulse">
          <Activity className="w-8 h-8" />
        </div>
        <p className="text-white font-medium">Computing proactive statistical briefing &amp; finding extraction...</p>
      </div>
    );
  }

  if (!briefing) {
    return (
      <div className="max-w-3xl mx-auto py-20 text-center space-y-4">
        <div className="inline-block p-4 rounded-2xl bg-slate-800 text-slate-400">
          <Database className="w-8 h-8" />
        </div>
        <h3 className="text-lg font-bold text-white">No Briefing Loaded</h3>
        <p className="text-slate-400 text-sm">
          Please upload or select a dataset to compute autonomous data quality and statistical profiling.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 space-y-8">
      {/* Executive Health Overview */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-black text-white">{briefing.title || "Executive Dataset Briefing"}</h1>
            <p className="text-sm text-slate-400 max-w-3xl">{briefing.summary}</p>
          </div>
          <div className="flex items-center space-x-2 bg-emerald-500/10 border border-emerald-500/20 px-3.5 py-1.5 rounded-full text-emerald-400 text-xs font-bold uppercase tracking-wider">
            <CheckCircle className="w-4 h-4" />
            <span>Profile Verified</span>
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Total Records</span>
            <p className="text-2xl font-black text-white mt-1">{briefing.row_count.toLocaleString()}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Columns</span>
            <p className="text-2xl font-black text-white mt-1">{briefing.column_count}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Key Findings</span>
            <p className="text-2xl font-black text-brand-400 mt-1">{briefing.findings?.length || 0}</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800">
            <span className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Recommended Charts</span>
            <p className="text-2xl font-black text-accent-400 mt-1">{briefing.recommended_charts?.length || 0}</p>
          </div>
        </div>

        {/* Action Recommendations */}
        {briefing.recommendations && briefing.recommendations.length > 0 && (
          <div className="p-4 rounded-xl bg-brand-500/5 border border-brand-500/15 space-y-2">
            <h3 className="text-xs font-bold uppercase tracking-wider text-brand-400 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Recommended Strategic Actions</span>
            </h3>
            <ul className="space-y-1 text-xs text-slate-300">
              {briefing.recommendations.map((rec, i) => (
                <li key={i} className="flex items-start space-x-2">
                  <span className="text-brand-400 font-bold">&bull;</span>
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Proactive Findings Grid */}
      <div className="space-y-4">
        <h2 className="text-lg font-bold text-white flex items-center space-x-2">
          <Layers className="w-5 h-5 text-brand-400" />
          <span>Proactive Statistical Findings</span>
        </h2>

        {(!briefing.findings || briefing.findings.length === 0) ? (
          <p className="text-sm text-slate-500">No outlier or strong correlation findings flagged.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {briefing.findings.map((f, i) => (
              <FindingCard
                key={f.id || i}
                finding={f}
                onDrillDownStarted={onDrillDown}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
