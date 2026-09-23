"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { DatasetUpload } from "@/components/DatasetUpload";
import { BriefingView } from "@/components/BriefingView";
import { ChatWorkspace } from "@/components/ChatWorkspace";
import { VisualizationsGallery } from "@/components/VisualizationsGallery";
import { ReportView } from "@/components/ReportView";
import { Dataset, DatasetBriefing, listDatasets, getBriefing, checkBackendHealth } from "@/lib/api";
import { AlertCircle, RefreshCw } from "lucide-react";

export default function Home() {
  const [activeTab, setActiveTab] = useState("upload");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined);
  const [briefing, setBriefing] = useState<DatasetBriefing | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  const loadBriefingForDataset = async (datasetId: string) => {
    setLoadingBriefing(true);
    try {
      const data = await getBriefing(datasetId);
      setBriefing(data);
    } catch {
      setBriefing(null);
    } finally {
      setLoadingBriefing(false);
    }
  };

  const refreshData = async () => {
    const isOnline = await checkBackendHealth();
    setBackendOnline(isOnline);
    if (isOnline) {
      const data = await listDatasets();
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        setSelectedDataset(data[0]);
        setActiveRunId(data[0].id);
        loadBriefingForDataset(data[0].id);
      }
    }
  };

  // Load datasets on mount
  useEffect(() => {
    refreshData();
  }, []);

  const handleDatasetSelected = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setActiveRunId(dataset.id);
    loadBriefingForDataset(dataset.id);
  };

  const handleDatasetUploaded = (datasetId: string, name: string) => {
    const newDs: Dataset = { id: datasetId, name, created_at: new Date().toISOString() };
    setDatasets((prev) => [newDs, ...prev]);
    setSelectedDataset(newDs);
    setActiveRunId(datasetId);
    setActiveTab("briefing");
    loadBriefingForDataset(datasetId);
  };

  const handleDrillDown = (result: any) => {
    setActiveTab("chat");
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        selectedDatasetName={selectedDataset?.name}
      />

      {/* Backend Offline Warning Banner */}
      {backendOnline === false && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5">
          <div className="max-w-7xl mx-auto flex items-center justify-between text-xs text-amber-300">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-400" />
              <span>
                <strong>FastAPI backend is offline:</strong> Start the backend server on port 8000 using <code className="bg-amber-950/60 px-1.5 py-0.5 rounded text-amber-200">.venv\Scripts\python -m uvicorn apps.api.app.main:app --reload</code> or <code className="bg-amber-950/60 px-1.5 py-0.5 rounded text-amber-200">docker compose up</code>.
              </span>
            </div>
            <button
              onClick={refreshData}
              className="flex items-center space-x-1 font-semibold underline hover:text-amber-100 ml-4 flex-shrink-0"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Connection</span>
            </button>
          </div>
        </div>
      )}

      <main className="flex-1">
        {activeTab === "upload" && (
          <DatasetUpload
            datasets={datasets}
            selectedDatasetId={selectedDataset?.id}
            onSelectDataset={handleDatasetSelected}
            onDatasetUploaded={handleDatasetUploaded}
          />
        )}

        {activeTab === "briefing" && (
          <BriefingView
            briefing={briefing}
            loading={loadingBriefing}
            onDrillDown={handleDrillDown}
          />
        )}

        {activeTab === "chat" && (
          <ChatWorkspace
            runId={activeRunId}
            onDrillDown={handleDrillDown}
          />
        )}

        {activeTab === "visualizations" && (
          <VisualizationsGallery
            charts={briefing?.recommended_charts || []}
            loading={loadingBriefing}
          />
        )}

        {activeTab === "report" && (
          <ReportView
            runId={activeRunId}
            datasetName={selectedDataset?.name}
          />
        )}
      </main>
    </div>
  );
}
