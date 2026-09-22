"use client";

import React, { useState } from "react";
import { ShieldCheck, Download, FileText, Loader2, Sparkles } from "lucide-react";
import { ReportItem, generateReport } from "@/lib/api";

interface ReportViewProps {
  runId?: string;
  datasetName?: string;
}

export const ReportView: React.FC<ReportViewProps> = ({
  runId,
  datasetName,
}) => {
  const [report, setReport] = useState<ReportItem | null>(null);
  const [generating, setGenerating] = useState(false);
  const [pinnedOnly, setPinnedOnly] = useState(false);

  const handleGenerate = async () => {
    if (!runId) return;
    setGenerating(true);
    try {
      const res = await generateReport(
        runId,
        `Executive Analysis Report: ${datasetName || "Dataset"}`,
        pinnedOnly,
      );
      setReport(res);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const downloadFile = (content: string, filename: string, type: string) => {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (!runId) {
    return (
      <div className="max-w-3xl mx-auto py-20 text-center space-y-3">
        <ShieldCheck className="w-10 h-10 text-brand-400 mx-auto" />
        <h3 className="text-lg font-bold text-white">Select a Dataset to Generate Reports</h3>
        <p className="text-slate-400 text-sm">
          Export full publication-ready Markdown and standalone HTML executive summaries.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-8">
      {/* Action Header */}
      <div className="glass-panel p-6 sm:p-8 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-white">Executive Report Generator</h1>
          <p className="text-sm text-slate-400">
            Compile verified evidence, briefing metrics, drill-down deep dives, and visualizations into an exportable document.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
            <input
              type="checkbox"
              checked={pinnedOnly}
              onChange={(e) => setPinnedOnly(e.target.checked)}
              className="rounded bg-slate-800 border-slate-700 text-brand-500 focus:ring-0"
            />
            <span>Pinned findings only</span>
          </label>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-400 disabled:opacity-50 text-black font-bold text-sm shadow-lg shadow-brand-500/20 transition-all"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4" />
            )}
            <span>{generating ? "Compiling..." : "Generate Report"}</span>
          </button>
        </div>
      </div>

      {/* Generated Report Viewer */}
      {report && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white flex items-center space-x-2">
              <FileText className="w-5 h-5 text-brand-400" />
              <span>Report Preview</span>
            </h2>

            <div className="flex space-x-2">
              {report.markdown_content && (
                <button
                  onClick={() => downloadFile(report.markdown_content!, "analysis_report.md", "text/markdown")}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Markdown</span>
                </button>
              )}
              {report.html_content && (
                <button
                  onClick={() => downloadFile(report.html_content!, "analysis_report.html", "text/html")}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-accent-500/20 hover:bg-accent-500/30 text-accent-400 border border-accent-500/40 text-xs font-semibold"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download HTML</span>
                </button>
              )}
            </div>
          </div>

          <div className="glass-panel p-8 rounded-2xl overflow-hidden">
            <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap leading-relaxed max-h-[600px] overflow-y-auto">
              {report.markdown_content}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
