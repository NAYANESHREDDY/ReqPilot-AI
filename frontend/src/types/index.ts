export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
}

export interface Project {
  id: string;
  title: string;
  description: string;
  domain: string;
  status: string;
  health_score: number;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  total_requirements: number;
  approved_requirements: number;
  needs_review_requirements: number;
  open_issues: number;
  conflict_count: number;
  ambiguity_count: number;
  total_tasks: number;
  completed_tasks: number;
  average_quality_score: number;
  health_score: number;
}

export interface DocumentChunk {
  id: string;
  chunk_index: number;
  section_title: string;
  page_number: number;
  content: string;
  token_count: number;
}

export interface DocumentItem {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  created_at: string;
  chunks?: DocumentChunk[];
}

export interface Requirement {
  id: string;
  project_id: string;
  req_type: 'functional' | 'non_functional' | 'constraint' | 'business_rule';
  summary: string;
  description: string;
  actor: string;
  action: string;
  target_object: string;
  preconditions: string;
  expected_outcome: string;
  acceptance_criteria: string[];
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'needs_review' | 'approved' | 'rejected' | 'modified';
  quality_score: number;
  quality_breakdown: Record<string, number>;
  confidence: number;
  is_ai_suggested: boolean;
  version: number;
  source_id: string;
  source_page: number;
  source_excerpt: string;
  created_at: string;
  updated_at: string;
}

export interface RequirementIssue {
  id: string;
  project_id: string;
  requirement_id?: string;
  conflict_with_id?: string;
  issue_type: 'ambiguity' | 'conflict' | 'duplicate' | 'incompleteness' | 'testability' | 'feasibility';
  title: string;
  description: string;
  detected_phrase: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  status: 'open' | 'resolved' | 'dismissed';
  resolution_note: string;
  created_at: string;
}

export interface ClarificationQuestion {
  id: string;
  project_id: string;
  requirement_id?: string;
  question: string;
  rationale: string;
  priority: 'high' | 'medium' | 'low';
  suggested_options: string[];
  answer: string;
  answered_by: string;
  status: 'pending' | 'answered' | 'dismissed';
  created_at: string;
  answered_at?: string;
}

export interface ArchitectureModule {
  id: string;
  name: string;
  description: string;
  module_type: 'service' | 'database' | 'ui' | 'external_api' | 'gateway';
  tech_stack: string;
  responsibilities: string[];
  api_endpoints: string[];
  pos_x: number;
  pos_y: number;
  is_ai_suggested: boolean;
  status: string;
}

export interface ArchitectureRelation {
  id: string;
  source_module_id: string;
  target_module_id: string;
  relation_type: string;
  description: string;
}

export interface Task {
  id: string;
  project_id: string;
  epic_id?: string;
  feature_id?: string;
  requirement_id?: string;
  module_id?: string;
  title: string;
  description: string;
  complexity: 'low' | 'medium' | 'high';
  estimated_hours: number;
  story_points: number;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'review' | 'done';
  assignee_name: string;
  sprint_name: string;
  subtasks: string[];
  acceptance_criteria: string[];
  depends_on?: string[];
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: string;
  capacity_hours_per_week: number;
  current_load_pct: number;
  skills: Record<string, number>;
}

export interface TraceabilityMatrixRow {
  source_id: string;
  source_page: number;
  requirement_id: string;
  requirement_summary: string;
  req_type: string;
  status: string;
  module_id?: string;
  module_name?: string;
  task_ids: string[];
  test_ids: string[];
  is_orphan: boolean;
}

export interface TraceabilityResponse {
  matrix: TraceabilityMatrixRow[];
  total_requirements: number;
  fully_linked_count: number;
  orphan_count: number;
  coverage_pct: number;
}

export interface ImpactItem {
  id: string;
  artifact_type: string;
  artifact_id: string;
  artifact_name: string;
  impact_description: string;
  severity: string;
}

export interface ChangeRequest {
  id: string;
  project_id: string;
  requirement_id: string;
  title: string;
  description: string;
  proposed_summary: string;
  proposed_description: string;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  schedule_impact: string;
  status: string;
  created_at: string;
  impact_items: ImpactItem[];
}

export interface ReportItem {
  id: string;
  project_id: string;
  report_type: 'srs' | 'quality_audit' | 'architecture' | 'plan' | 'traceability' | 'change_impact';
  title: string;
  content_markdown: string;
  created_at: string;
}

export interface BaselineComparison {
  system_name: string;
  extraction_f1: number;
  conflict_f1: number;
  ambiguity_f1: number;
  hallucination_rate_pct: number;
  avg_latency_seconds: number;
}

export interface EvaluationResult {
  requirement_extraction: {
    precision: number;
    recall: number;
    f1_score: number;
    accuracy: number;
    total_samples: number;
  };
  ambiguity_detection: {
    precision: number;
    recall: number;
    f1_score: number;
    accuracy: number;
    total_samples: number;
  };
  conflict_detection: {
    precision: number;
    recall: number;
    f1_score: number;
    accuracy: number;
    total_samples: number;
  };
  duplicate_detection: {
    precision: number;
    recall: number;
    f1_score: number;
    accuracy: number;
    total_samples: number;
  };
  traceability_coverage_pct: number;
  baseline_comparisons: BaselineComparison[];
  tested_at: string;
}
