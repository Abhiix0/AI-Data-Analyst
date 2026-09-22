"use client";

import React from "react";
import { Database, Activity, ShieldCheck, Sparkles } from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  selectedDatasetName?: string;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab, selectedDatasetName }) => {
  const tabs = [
    { id: "upload", label: "Datasets & Ingestion", icon: Database },
    { id: "briefing", label: "Dataset Briefing", icon: Activity },
    { id: "chat", label: "Analytical Agent & Chat", icon: Sparkles },
    { id: "visualizations", label: "Visualizations", icon: Activity },
    { id: "report", label: "Executive Report", icon: ShieldCheck },
  ];

  return (
    <header className="border-b border-surface-border bg-surface/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-accent-400 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-lg bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  AI Data Analyst
                </span>
                <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider uppercase rounded-full bg-brand-500/10 text-brand-400 border border-brand-500/20">
                  Evidence-Gated
                </span>
              </div>
              {selectedDatasetName && (
                <p className="text-xs text-slate-400 truncate max-w-xs">
                  Active: <span className="text-slate-200 font-medium">{selectedDatasetName}</span>
                </p>
              )}
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all ${
                    isActive
                      ? "bg-brand-500/15 text-brand-400 border border-brand-500/30 shadow-sm shadow-brand-500/10"
                      : "text-slate-400 hover:text-slate-200 hover:bg-surface-raised"
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
};
