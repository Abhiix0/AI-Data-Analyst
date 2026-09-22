"use client";

import React, { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { DatasetUpload } from "@/components/DatasetUpload";
import { BriefingView } from "@/components/BriefingView";
import { ChatWorkspace } from "@/components/ChatWorkspace";
import { VisualizationsGallery } from "@/components/VisualizationsGallery";
import { ReportView } from "@/components/ReportView";
import { Dataset, DatasetBriefing, listDatasets } from "@/lib/api";

export default function Home() {
  const [activeTab, setActiveTab] = useState("upload");
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | undefined>(undefined);
  const [briefing, setBriefing] = useState<DatasetBriefing | null>(null);
  const [loadingBriefing, setLoadingBriefing] = useState(false);

  // Load datasets on mount
  useEffect(() => {
    listDatasets().then((data) => {
      setDatasets(data);
      if (data.length > 0 && !selectedDataset) {
        setSelectedDataset(data[0]);
        setActiveRunId(data[0].id);
      }
    });
  }, []);

  const handleDatasetSelected = (dataset: Dataset) => {
    setSelectedDataset(dataset);
    setActiveRunId(dataset.id);
  };

  const handleDatasetUploaded = (datasetId: string, name: string) => {
    const newDs: Dataset = { id: datasetId, name, created_at: new Date().toISOString() };
    setDatasets((prev) => [newDs, ...prev]);
    setSelectedDataset(newDs);
    setActiveRunId(datasetId);
    setActiveTab("briefing");
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
