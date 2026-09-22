"use client";

import React from "react";
import { ShieldCheck, X, CheckCircle2, Terminal } from "lucide-react";
import { EvidenceItem } from "@/lib/api";

interface EvidenceLedgerDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: EvidenceItem[];
}

export const EvidenceLedgerDrawer: React.FC<EvidenceLedgerDrawerProps> = ({
  isOpen,
  onClose,
  evidence,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity">
      <div className="w-full max-w-xl h-full bg-slate-900 border-l border-slate-800 shadow-2xl flex flex-col">
        {/* Drawer Header */}
        <div className="p-6 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 rounded-lg bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Verified Evidence Ledger</h2>
              <p className="text-xs text-slate-400">Deterministic tool outputs &amp; zero-hallucination audit trail</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Ledger Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {evidence.length === 0 ? (
            <div className="text-center py-12 text-slate-500 text-sm">
              No evidence recorded yet. Run an analysis or chat query to populate the ledger.
            </div>
          ) : (
            evidence.map((ev, i) => (
              <div
                key={ev.id || i}
                className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-3"
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs text-brand-400 font-semibold">{ev.metric_name}</span>
                  <span className="flex items-center space-x-1 text-[11px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>{(ev.confidence_score * 100).toFixed(0)}% verified</span>
                  </span>
                </div>

                <div className="p-2.5 rounded-lg bg-black/50 border border-slate-800/80 font-mono text-sm text-white">
                  {typeof ev.value === "object" ? JSON.stringify(ev.value, null, 2) : String(ev.value)}
                </div>

                {(ev.source_query || ev.source_tool) && (
                  <div className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                    <Terminal className="w-3.5 h-3.5 text-slate-500 flex-shrink-0" />
                    <span className="truncate">{ev.source_query || ev.source_tool}</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
