export interface District {
  id: number;
  city_id: string;
  name: string;
  geojson?: object;
}

export interface CityScore {
  id: number;
  city_id: string;
  district_id: number;
  timestamp: string;
  traffic_score: number;
  environment_score: number;
  citizen_score: number;
  risk_score: number;
  overall_score: number;
}

export interface EvidenceItem {
  id: string;
  agent: string;
  source: string;
  type: string;
  content: string;
  confidence: number;
  time: string;
}

export interface DecisionOut {
  prediction: Record<string, string>;
  impact: Record<string, string>;
  recommendations: string[];
  confidence: number;
  explanation: string[];
  evidence: EvidenceItem[];
}

export type SimulationScenario = 'heavy_rain' | 'air_pollution' | 'major_event' | 'heatwave' | 'earthquake' | 'flood' | 'festival';

export interface AQIPoint {
  time: string;
  aqi_index: number;
  pm25: number;
}

export interface AgentDecisionOut {
  id: number;
  city_id: string;
  district_id: number | null;
  query: string | null;
  prediction: Record<string, string> | null;
  impact: Record<string, string> | null;
  recommendations: string[] | null;
  confidence: number | null;
  explanation: string[] | null;
  evidence: EvidenceItem[] | null;
  requires_approval: boolean;
  approved: boolean | null;
  created_at: string | null;
}

export interface AgentEvent {
  type: 'pipeline_start' | 'agent_update' | 'pipeline_done' | 'approval_needed' | 'approval_result';
  agent: string;
  status: 'planning' | 'running' | 'done' | 'waiting' | 'approved' | 'rejected';
  detail: string;
  ts: string;
}

// ── CityOS v2 Autonomous Runtime ──────────────────────────────────────

export type RuntimeTaskStatus = 'pending' | 'running' | 'done' | 'failed';

export type RuntimeRunStatus =
  | 'planning' | 'running' | 'reflecting' | 'deciding'
  | 'awaiting_approval' | 'executing_workflow'
  | 'done' | 'failed' | 'rejected';

export interface RuntimeTask {
  id: string;
  agent: string;
  depends_on: string[];
  priority: number;
  status: RuntimeTaskStatus;
  attempts: number;
  result: Record<string, unknown> | null;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  latency_ms: number | null;
}

export interface RuntimeEvidence {
  task: string;
  agent: string;
  summary: string;
  confidence: number | null;
}

export interface RuntimeDecision {
  summary: string;
  prediction: string;
  risk: 'low' | 'medium' | 'high';
  recommendation: string[];
  confidence: number;
  evidence: RuntimeEvidence[];
}

export interface WorkflowStep {
  step: string;
  detail: string;
  ts: string;
}

export interface TimelineEntry {
  ts: string;
  actor: string;
  message: string;
}

export interface RuntimeRun {
  run_id: string;
  goal: string;
  district_id: number;
  status: RuntimeRunStatus;
  tasks: RuntimeTask[];
  decision: RuntimeDecision | null;
  workflow_steps: WorkflowStep[];
  timeline: TimelineEntry[];
  created_at: string;
  decision_record_id: number | null;
  reflection: { avg_confidence: number; notes: string[]; missing: string[] } | null;
}

export interface RuntimeRunSummary {
  run_id: string;
  goal: string;
  district_id: number;
  status: RuntimeRunStatus;
  created_at: string;
  task_count: number;
  confidence: number | null;
}

export interface SimulationStatus {
  running: boolean;
  scenario: string;
  scenario_label: string;
  interval_s: number;
  auto_goal: boolean;
  tick: number;
  values: { rain: number; aqi: number; temperature: number; humidity: number; wind_speed: number };
  last_auto_goal: string | null;
}

export interface ScenarioInfo {
  name: string;
  label: string;
}

export type CrawlResults = Record<string, { ok: boolean; count?: number; error?: string }>;

export interface RuntimeMonitor {
  agents: Record<string, {
    runs: number;
    failures: number;
    avg_latency_ms: number | null;
    last_status: string;
  }>;
  active_runs: number;
  total_runs: number;
}
