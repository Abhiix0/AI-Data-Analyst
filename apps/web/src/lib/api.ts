/** Typed API Client for AI Data Analyst Backend */

export interface Dataset {
  id: string;
  name: string;
  created_at: string;
  versions_count?: number;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_num: number;
  row_count: number;
  col_count: number;
  schema_json: Record<string, string>;
  created_at: string;
}

export interface EvidenceItem {
  id: string;
  metric_name: string;
  value: any;
  source_query?: string;
  source_tool?: string;
  confidence_score: number;
}

export interface FindingItem {
  id: string;
  run_id?: string;
  claim: string;
  evidence_json?: EvidenceItem[];
  evidence_strength: string;
  source_columns?: string[];
  is_pinned?: boolean;
  user_notes?: string | null;
  parent_finding_id?: string | null;
  title?: string;
  description?: string;
  strength?: string;
  evidence_ids?: string[];
}

export interface DatasetBriefing {
  title: string;
  summary: string;
  row_count: number;
  column_count: number;
  findings: FindingItem[];
  recommendations: string[];
  recommended_charts: any[];
}

export interface ChatTurn {
  id: string;
  run_id: string;
  turn_index: number;
  user_message: string;
  assistant_message: string;
  findings: any[];
  evidence: EvidenceItem[];
  created_at: string;
}

export interface InvestigationItem {
  id: string;
  run_id: string;
  parent_finding_id?: string | null;
  query: string;
  status: string;
  findings_count: number;
  summary?: string;
  created_at: string;
}

export interface ReportItem {
  id: string;
  run_id: string;
  storage_path: string;
  markdown_path?: string;
  html_path?: string;
  markdown_content?: string;
  html_content?: string;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api";

export async function uploadDataset(file: File): Promise<{ dataset_id: string; version_id: string; row_count: number; col_count: number }> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/datasets/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Upload failed");
  }
  return res.json();
}

export async function listDatasets(): Promise<Dataset[]> {
  const res = await fetch(`${API_BASE}/datasets`);
  if (!res.ok) return [];
  return res.json();
}

export async function askQuestion(runOrDatasetId: string, question: string): Promise<{
  run_id: string;
  question: string;
  answer: string;
  validation_passed: boolean;
  findings: any[];
  evidence: EvidenceItem[];
}> {
  const res = await fetch(`${API_BASE}/runs/${runOrDatasetId}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed" }));
    throw new Error(err.detail || "Query failed");
  }
  return res.json();
}

export async function sendChatMessage(runId: string, message: string): Promise<ChatTurn> {
  const res = await fetch(`${API_BASE}/runs/${runId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Chat failed" }));
    throw new Error(err.detail || "Chat failed");
  }
  return res.json();
}

export async function getChatHistory(runId: string): Promise<ChatTurn[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/chat/history`);
  if (!res.ok) return [];
  return res.json();
}

export async function listRunFindings(runId: string, isPinned?: boolean): Promise<FindingItem[]> {
  const url = isPinned !== undefined
    ? `${API_BASE}/runs/${runId}/findings?is_pinned=${isPinned}`
    : `${API_BASE}/runs/${runId}/findings`;
  const res = await fetch(url);
  if (!res.ok) return [];
  return res.json();
}

export async function updateFinding(findingId: string, updates: { is_pinned?: boolean; user_notes?: string }): Promise<FindingItem> {
  const res = await fetch(`${API_BASE}/findings/${findingId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(updates),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Update finding failed" }));
    throw new Error(err.detail || "Update finding failed");
  }
  return res.json();
}

export async function investigateFinding(findingId: string): Promise<{
  investigation_id: string;
  parent_finding_id: string;
  parent_claim: string;
  investigation_query: string;
  answer: string;
  validation_passed: boolean;
  new_findings: any[];
  evidence: EvidenceItem[];
}> {
  const res = await fetch(`${API_BASE}/findings/${findingId}/investigate`, {
    method: "POST",
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Drill-down investigation failed" }));
    throw new Error(err.detail || "Drill-down investigation failed");
  }
  return res.json();
}

export async function listRunInvestigations(runId: string): Promise<InvestigationItem[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/investigations`);
  if (!res.ok) return [];
  return res.json();
}

export async function generateReport(runId: string, title?: string, pinnedOnly?: boolean): Promise<ReportItem> {
  const res = await fetch(`${API_BASE}/runs/${runId}/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: title || "Executive Analysis Report",
      include_pinned_only: !!pinnedOnly,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Report generation failed" }));
    throw new Error(err.detail || "Report generation failed");
  }
  return res.json();
}

export async function listRunReports(runId: string): Promise<ReportItem[]> {
  const res = await fetch(`${API_BASE}/runs/${runId}/reports`);
  if (!res.ok) return [];
  return res.json();
}
