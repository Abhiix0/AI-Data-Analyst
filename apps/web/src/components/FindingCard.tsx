"use client";

import React, { useState } from "react";
import { Bookmark, Sparkles, ChevronDown, ChevronUp, FileText, CheckCircle, Search } from "lucide-react";
import { FindingItem, updateFinding, investigateFinding } from "@/lib/api";

interface FindingCardProps {
  finding: FindingItem;
  onFindingUpdated?: (updated: FindingItem) => void;
  onDrillDownStarted?: (result: any) => void;
}

export const FindingCard: React.FC<FindingCardProps> = ({
  finding,
  onFindingUpdated,
  onDrillDownStarted,
}) => {
  const [isPinned, setIsPinned] = useState(!!finding.is_pinned);
  const [notes, setNotes] = useState(finding.user_notes || "");
  const [isEditingNotes, setIsEditingNotes] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [investigating, setInvestigating] = useState(false);

  const strength = (finding.evidence_strength || finding.strength || "strong").toLowerCase();
  const strengthColor =
    strength === "strong"
      ? "bg-emerald-500/15 text-emerald-400 border-emerald-500/30"
      : strength === "moderate"
      ? "bg-amber-500/15 text-amber-400 border-amber-500/30"
      : "bg-rose-500/15 text-rose-400 border-rose-500/30";

  const togglePin = async () => {
    const nextVal = !isPinned;
    setIsPinned(nextVal);
    try {
      const updated = await updateFinding(finding.id, { is_pinned: nextVal });
      if (onFindingUpdated) onFindingUpdated(updated);
    } catch (e) {
      setIsPinned(!nextVal);
    }
  };

  const saveNotes = async () => {
    try {
      const updated = await updateFinding(finding.id, { user_notes: notes });
      setIsEditingNotes(false);
      if (onFindingUpdated) onFindingUpdated(updated);
    } catch (e) {
      console.error(e);
    }
  };

  const handleInvestigate = async () => {
    setInvestigating(true);
    try {
      const res = await investigateFinding(finding.id);
      if (onDrillDownStarted) onDrillDownStarted(res);
    } catch (e) {
      console.error(e);
    } finally {
      setInvestigating(false);
    }
  };

  return (
    <div className="glass-card rounded-xl p-5 space-y-3 transition-all border border-slate-700/60 hover:border-slate-600">
      {/* Header Row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center space-x-2">
          <span className={`px-2.5 py-0.5 text-[11px] font-bold uppercase rounded-full border ${strengthColor}`}>
            {strength}
          </span>
          {finding.source_columns && finding.source_columns.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {finding.source_columns.slice(0, 3).map((col) => (
                <span key={col} className="px-2 py-0.5 text-[10px] rounded bg-slate-800 text-slate-300 font-mono">
                  {col}
                </span>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={togglePin}
          title={isPinned ? "Unpin finding" : "Pin finding"}
          className={`p-1.5 rounded-lg transition-colors ${
            isPinned ? "bg-amber-500/20 text-amber-400" : "text-slate-500 hover:text-slate-300 hover:bg-slate-800"
          }`}
        >
          <Bookmark className={`w-4 h-4 ${isPinned ? "fill-amber-400" : ""}`} />
        </button>
      </div>

      {/* Claim / Title */}
      <p className="text-sm font-semibold text-white leading-relaxed">
        {finding.claim || finding.title || "Analytical Finding"}
      </p>

      {/* Description if separate */}
      {finding.description && finding.description !== finding.claim && (
        <p className="text-xs text-slate-300 leading-normal">
          {finding.description}
        </p>
      )}

      {/* User Notes */}
      {finding.user_notes && !isEditingNotes && (
        <div className="p-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs text-slate-300 italic flex items-start space-x-2">
          <FileText className="w-3.5 h-3.5 text-brand-400 mt-0.5 flex-shrink-0" />
          <span>&ldquo;{finding.user_notes}&rdquo;</span>
        </div>
      )}

      {/* Notes Editor */}
      {isEditingNotes && (
        <div className="space-y-2 pt-1">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add user reflections, hypothesis, or follow-up notes..."
            className="w-full text-xs p-2 rounded-lg bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-brand-400"
            rows={2}
          />
          <div className="flex justify-end space-x-2">
            <button
              onClick={() => setIsEditingNotes(false)}
              className="px-2.5 py-1 text-xs text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={saveNotes}
              className="px-3 py-1 text-xs font-semibold rounded-md bg-brand-500 text-black hover:bg-brand-400"
            >
              Save Note
            </button>
          </div>
        </div>
      )}

      {/* Action Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-xs">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsEditingNotes(!isEditingNotes)}
            className="text-slate-400 hover:text-brand-400 font-medium transition-colors"
          >
            {finding.user_notes ? "Edit Note" : "+ Add Note"}
          </button>
          {finding.evidence_json && finding.evidence_json.length > 0 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-slate-400 hover:text-slate-200 flex items-center space-x-1"
            >
              <span>{finding.evidence_json.length} Evidence</span>
              {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>
          )}
        </div>

        <button
          onClick={handleInvestigate}
          disabled={investigating}
          className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-accent-500/10 hover:bg-accent-500/20 text-accent-400 border border-accent-500/30 transition-all font-medium"
        >
          <Search className="w-3.5 h-3.5" />
          <span>{investigating ? "Drilling down..." : "Deep Dive"}</span>
        </button>
      </div>

      {/* Expanded Evidence Details */}
      {isExpanded && finding.evidence_json && (
        <div className="mt-2 p-3 rounded-lg bg-black/40 border border-slate-800 space-y-2 text-xs">
          <p className="font-semibold text-slate-300">Verified Evidence Ledger:</p>
          {finding.evidence_json.map((ev, i) => (
            <div key={i} className="flex items-center justify-between text-slate-400 font-mono text-[11px]">
              <span>{ev.metric_name} = <strong className="text-white">{String(ev.value)}</strong></span>
              <span className="text-slate-500">{(ev.confidence_score * 100).toFixed(0)}% conf</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
