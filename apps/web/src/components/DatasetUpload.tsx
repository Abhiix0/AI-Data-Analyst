"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, FileSpreadsheet, CheckCircle2, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { uploadDataset, Dataset } from "@/lib/api";

interface DatasetUploadProps {
  onDatasetUploaded: (datasetId: string, name: string) => void;
  datasets: Dataset[];
  selectedDatasetId?: string;
  onSelectDataset: (dataset: Dataset) => void;
}

export const DatasetUpload: React.FC<DatasetUploadProps> = ({
  onDatasetUploaded,
  datasets,
  selectedDatasetId,
  onSelectDataset,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploadError(null);
    setUploadSuccess(null);
    setUploading(true);

    try {
      const res = await uploadDataset(file);
      setUploadSuccess(`Successfully ingested "${file.name}" with ${res.row_count.toLocaleString()} rows and ${res.col_count} columns.`);
      onDatasetUploaded(res.dataset_id, file.name);
    } catch (err: any) {
      setUploadError(err.message || "Failed to upload dataset.");
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="max-w-5xl mx-auto py-8 px-4 space-y-8">
      {/* Hero Banner */}
      <div className="text-center space-y-3">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
          Ingest &amp; Analyze Any Tabular Dataset
        </h1>
        <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto">
          Upload CSV, TSV, or Excel files. Automated type inference, schema validation, and Polars parity engine process your data instantly.
        </p>
      </div>

      {/* Upload Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`glass-panel rounded-2xl p-8 sm:p-12 text-center cursor-pointer transition-all border-2 border-dashed ${
          isDragging
            ? "border-brand-400 bg-brand-500/10 scale-[1.01]"
            : "border-slate-700 hover:border-slate-500 hover:bg-surface-raised"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".csv,.tsv,.xlsx,.xls"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />

        <div className="flex flex-col items-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-brand-500/10 border border-brand-500/20 flex items-center justify-center text-brand-400 shadow-inner">
            {uploading ? (
              <Loader2 className="w-8 h-8 animate-spin" />
            ) : (
              <UploadCloud className="w-8 h-8" />
            )}
          </div>
          <div>
            <p className="text-base font-semibold text-white">
              {uploading ? "Ingesting dataset via Polars engine..." : "Drop your dataset here, or browse"}
            </p>
            <p className="text-xs text-slate-400 mt-1">
              Supports CSV, TSV, and Excel up to 500 MB &bull; Strict deterministic parsing
            </p>
          </div>
        </div>
      </div>

      {/* Status Alerts */}
      {uploadError && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 flex items-center space-x-3 text-sm">
          <AlertCircle className="w-5 h-5 flex-shrink-0" />
          <span>{uploadError}</span>
        </div>
      )}

      {uploadSuccess && (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center space-x-3 text-sm">
          <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}

      {/* Existing Datasets List */}
      {datasets.length > 0 && (
        <div className="space-y-4 pt-4">
          <h2 className="text-lg font-bold text-white flex items-center space-x-2">
            <FileSpreadsheet className="w-5 h-5 text-brand-400" />
            <span>Available Datasets</span>
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {datasets.map((d) => {
              const isSelected = d.id === selectedDatasetId;
              return (
                <div
                  key={d.id}
                  onClick={() => onSelectDataset(d)}
                  className={`glass-card p-5 rounded-xl cursor-pointer flex items-center justify-between group ${
                    isSelected ? "border-brand-400 bg-brand-500/10" : ""
                  }`}
                >
                  <div className="space-y-1">
                    <p className="font-semibold text-sm text-white group-hover:text-brand-400 transition-colors">
                      {d.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      Uploaded {new Date(d.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2 text-xs font-medium text-slate-400 group-hover:text-brand-400">
                    <span>{isSelected ? "Active" : "Select"}</span>
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
