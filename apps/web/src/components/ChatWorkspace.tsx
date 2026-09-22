"use client";

import React, { useState, useEffect, useRef } from "react";
import { Send, Sparkles, ShieldCheck, AlertCircle, Loader2, Bookmark, Terminal, Search } from "lucide-react";
import { ChatTurn, EvidenceItem, sendChatMessage, getChatHistory } from "@/lib/api";
import { FindingCard } from "@/components/FindingCard";
import { EvidenceLedgerDrawer } from "@/components/EvidenceLedgerDrawer";

interface ChatWorkspaceProps {
  runId?: string;
  onDrillDown: (res: any) => void;
}

export const ChatWorkspace: React.FC<ChatWorkspaceProps> = ({
  runId,
  onDrillDown,
}) => {
  const [messages, setMessages] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeEvidence, setActiveEvidence] = useState<EvidenceItem[]>([]);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (runId) {
      getChatHistory(runId).then((turns) => {
        setMessages(turns);
        // Collect all evidence
        const allEv = turns.flatMap((t) => t.evidence || []);
        setActiveEvidence(allEv);
      });
    }
  }, [runId]);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !runId || loading) return;

    const query = input.trim();
    setInput("");
    setLoading(true);

    try {
      const turn = await sendChatMessage(runId, query);
      setMessages((prev) => [...prev, turn]);
      if (turn.evidence) {
        setActiveEvidence((prev) => [...prev, ...turn.evidence]);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (!runId) {
    return (
      <div className="max-w-3xl mx-auto py-20 text-center space-y-3">
        <Sparkles className="w-10 h-10 text-brand-400 mx-auto animate-pulse" />
        <h3 className="text-lg font-bold text-white">Select a Dataset to Start Analysis</h3>
        <p className="text-slate-400 text-sm">
          The evidence-gated LangGraph agent will execute multi-turn analytical inquiries over DuckDB and Polars.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto py-6 px-4 flex flex-col h-[calc(100vh-8rem)]">
      {/* Evidence Ledger Quick Bar */}
      <div className="flex items-center justify-between p-3 mb-4 rounded-xl bg-slate-900/90 border border-slate-800">
        <div className="flex items-center space-x-2">
          <ShieldCheck className="w-4 h-4 text-brand-400" />
          <span className="text-xs font-semibold text-slate-300">
            Hard Evidence Gate: <strong className="text-emerald-400 font-bold">100% Deterministic Grounding</strong>
          </span>
        </div>
        <button
          onClick={() => setIsDrawerOpen(true)}
          className="text-xs font-medium text-brand-400 hover:text-brand-300 underline"
        >
          View Evidence Ledger ({activeEvidence.length})
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {messages.length === 0 && !loading && (
          <div className="text-center py-16 space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-brand-500/10 border border-brand-500/20 text-brand-400 mx-auto flex items-center justify-center shadow-lg">
              <Sparkles className="w-6 h-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Ask Analytical Questions</h3>
            <p className="text-slate-400 text-xs sm:text-sm max-w-md mx-auto">
              Try: &ldquo;What are the strongest correlations in this dataset?&rdquo; or &ldquo;Identify top outliers in revenue and compare segments.&rdquo;
            </p>
          </div>
        )}

        {messages.map((turn, i) => (
          <div key={turn.id || i} className="space-y-4">
            {/* User Message */}
            <div className="flex justify-end">
              <div className="max-w-xl rounded-2xl rounded-tr-none px-4 py-3 bg-brand-600 text-white text-sm font-medium shadow-md">
                {turn.user_message}
              </div>
            </div>

            {/* Assistant Message */}
            <div className="flex justify-start">
              <div className="max-w-3xl space-y-4 rounded-2xl rounded-tl-none p-5 bg-slate-900 border border-slate-800 text-slate-200 text-sm leading-relaxed shadow-lg">
                <div className="flex items-center space-x-2 pb-2 border-b border-slate-800 text-xs text-brand-400 font-semibold">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Data Analyst &bull; Turn {turn.turn_index + 1}</span>
                </div>

                <div className="whitespace-pre-wrap text-sm text-slate-100">
                  {turn.assistant_message}
                </div>

                {/* Extracted Findings Cards */}
                {turn.findings && turn.findings.length > 0 && (
                  <div className="space-y-2 pt-2">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-400">Synthesized Findings</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      {turn.findings.map((f: any, idx: number) => (
                        <FindingCard
                          key={f.id || idx}
                          finding={f}
                          onDrillDownStarted={onDrillDown}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center space-x-3 p-4 rounded-2xl bg-slate-900 border border-slate-800 text-slate-400 text-xs font-medium">
              <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
              <span>Executing deterministic DuckDB / Polars pipeline &amp; synthesizing findings...</span>
            </div>
          </div>
        )}

        <div ref={scrollRef} />
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} className="mt-4 pt-2">
        <div className="flex items-center gap-2 p-1.5 rounded-2xl bg-slate-900 border border-slate-700/80 focus-within:border-brand-400 shadow-xl">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask anything about your data (e.g. churn drivers, distribution, segment comparisons)..."
            disabled={loading}
            className="flex-1 bg-transparent px-4 py-2.5 text-sm text-white focus:outline-none placeholder-slate-500"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-3 rounded-xl bg-brand-500 hover:bg-brand-400 disabled:opacity-50 text-black transition-colors font-bold flex-shrink-0"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
      </form>

      {/* Evidence Ledger Drawer */}
      <EvidenceLedgerDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        evidence={activeEvidence}
      />
    </div>
  );
};
