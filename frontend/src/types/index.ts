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
  task?: string;
  agent: string;
  summary?: string;
  source?: string;
  type?: string;
  content?: string;
  confidence: number | null;
  time?: string;
}

export interface RuntimeDecision {
  summary: string;
  prediction: string;
  risk: 'low' | 'medium' | 'high';
  recommendation: string[];
  confidence: number;
  evidence: RuntimeEvidence[];
  critic_notes?: string[];
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
  district_id?: number;
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

// ── Decision Session ──────────────────────────────────────────────────

export type DecisionSessionStatus =
  | 'collecting' | 'analyzing' | 'recommend' | 'awaiting_approval'
  | 'rejected' | 'observing' | 'evaluated';

export interface DecisionSessionScores {
  traffic_score: number;
  environment_score: number;
  citizen_score: number;
  risk_score: number;
  overall_score: number;
}

export interface DecisionSessionOutcomeEvidence {
  source: string;
  type: string;
  metric: string;
  value: number;
  confidence: number;
  timestamp: string;
}

export interface DecisionSession {
  id: number;
  run_id: string;
  goal: string;
  district_id: number | null;
  status: DecisionSessionStatus;
  decision_id: number | null;
  baseline_scores: DecisionSessionScores | null;
  expected_outcome: DecisionSessionScores | null;
  observed_scores: DecisionSessionScores | null;
  outcome_delta: Partial<DecisionSessionScores> | null;
  success_rate: number | null;
  outcome_status: 'improved' | 'no_change' | 'worse' | null;
  context_snapshot: Record<string, unknown> | null;
  outcome_evidence: DecisionSessionOutcomeEvidence[] | null;
  created_at: string | null;
  approved_at: string | null;
  observed_at: string | null;
  evaluated_at: string | null;
}

export interface SystemStatus {
  database: boolean;
  gemini_configured: boolean;
  neo4j_configured: boolean;
  qdrant_configured: boolean;
  openrouter_configured: boolean;
  gemini_model: string;
  gemini_temperature: number;
  openrouter_fallback_models: string[];
}

export interface KnowledgeRelatedItem {
  name: string | null;
  label: string | null;
  relation: string | null;
  related_name: string | null;
  rel_source: string | null;
  rel_confidence: number | null;
  rel_created_at: string | null;
}

export interface KnowledgeSummary {
  configured: boolean;
  entities: number;
  relations: number;
  sample: KnowledgeRelatedItem[];
}

export interface DecisionSessionAnalytics {
  total_sessions: number;
  approval_rate: number | null;
  evaluated_count: number;
  improved_rate: number | null;
  avg_improvement: number | null;
  avg_decision_latency_minutes: number | null;
}
