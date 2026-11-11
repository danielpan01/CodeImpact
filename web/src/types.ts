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
  evidence_edges: string[];
  path_revision: "before" | "after" | "both" | "mixed";
}
export interface SourceRange {
  line: number;
  end_line: number;
}
export interface SourceRevision {
  text: string;
  parse_status: "parsed" | "unparseable";
}
export interface SymbolChange {
  symbol: string;
  path: string;
  status: "added" | "modified" | "removed";
  before: SourceRange | null;
  after: SourceRange | null;
}
export interface DependencyEvidence {
  text: string;
  location: SourceRange & { path: string };
  target_location: SourceRange & { path: string };
}
export interface DependencyEdge {
  id: string;
  source: string;
  target: string;
  kind: "call" | "import" | "module";
  revision: "before" | "after" | "both";
  before: DependencyEvidence[];
  after: DependencyEvidence[];
}
export interface Report {
  source?: {
    kind: "github_pr";
    repository: string;
    head_repository: string;
    pr_number: number;
    pr_url: string;
    title: string;
    base_sha: string;
    head_sha: string;
    merge_base_sha: string;
    analyzer_version: string;
  };
  schema_version: "2.0";
  label: string;
  nodes: SymbolNode[];
  edges: DependencyEdge[];
  changed: string[];
  changes: SymbolChange[];
  source_files: {
    path: string;
    before: SourceRevision | null;
    after: SourceRevision | null;
  }[];
  removed: string[];
  impacted: string[];
  recommendations: Recommendation[];
  warnings: string[];
  stats: Record<string, number>;
}
