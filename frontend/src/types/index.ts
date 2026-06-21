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

export interface DecisionOut {
  prediction: Record<string, string>;
  impact: Record<string, string>;
  recommendations: string[];
  confidence: number;
  explanation: string[];
}

export type SimulationScenario = 'heavy_rain' | 'air_pollution' | 'major_event' | 'heatwave';

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
  created_at: string | null;
}
