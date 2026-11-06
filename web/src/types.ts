export interface SymbolNode {
  id: string;
  name: string;
  path: string;
  line: number;
  end_line: number;
  kind: "module" | "function" | "class" | "test";
}
export interface Recommendation {
  symbol: string;
  score: number;
  distance: number;
  reason: string;
  evidence_path: string[];
}
export interface Report {
  schema_version: string;
  label: string;
  nodes: SymbolNode[];
  edges: { source: string; target: string; kind: string; evidence: string }[];
  changed: string[];
  removed: string[];
  impacted: string[];
  recommendations: Recommendation[];
  warnings: string[];
  stats: Record<string, number>;
}
