import {
  Project, ProjectStats, DocumentItem, Requirement, RequirementIssue,
  ClarificationQuestion, ArchitectureModule, ArchitectureRelation, Task,
  TeamMember, TraceabilityResponse, ChangeRequest, ReportItem, EvaluationResult
} from '../types';

const API_BASE = '/api';

export const api = {
  // Auth
  async login(email: string, password: string) {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Login failed');
    return res.json();
  },

  async getCurrentUser() {
    const res = await fetch(`${API_BASE}/auth/me`);
    if (!res.ok) throw new Error('Failed to get user');
    return res.json();
  },

  // Projects
  async getProjects(): Promise<Project[]> {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  },

  async createProject(title: string, description: string, domain: string): Promise<Project> {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, description, domain }),
    });
    if (!res.ok) throw new Error('Failed to create project');
    return res.json();
  },

  async getProjectStats(projectId: string): Promise<ProjectStats> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/stats`);
    if (!res.ok) throw new Error('Failed to fetch project stats');
    return res.json();
  },

  // Documents
  async getDocuments(projectId: string): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async uploadDocument(projectId: string, file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/projects/${projectId}/documents/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Document upload failed');
    return res.json();
  },

  // Workflow / Multi-Agent Analysis
  async triggerAnalysis(projectId: string, useLlm: boolean = false, apiKey?: string, provider: string = 'gemini') {
    const res = await fetch(`${API_BASE}/projects/${projectId}/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ use_llm: useLlm, api_key: apiKey, provider }),
    });
    if (!res.ok) throw new Error('Analysis execution failed');
    return res.json();
  },

  // Requirements
  async getRequirements(projectId: string): Promise<Requirement[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/requirements`);
    if (!res.ok) throw new Error('Failed to fetch requirements');
    return res.json();
  },

  async createRequirement(projectId: string, data: Partial<Requirement>): Promise<Requirement> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/requirements`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to create requirement');
    return res.json();
  },

  async updateRequirement(id: string, data: Partial<Requirement>): Promise<Requirement> {
    const res = await fetch(`${API_BASE}/requirements/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error('Failed to update requirement');
    return res.json();
  },

  async approveRequirement(id: string): Promise<Requirement> {
    const res = await fetch(`${API_BASE}/requirements/${id}/approve`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to approve requirement');
    return res.json();
  },

  async rejectRequirement(id: string): Promise<Requirement> {
    const res = await fetch(`${API_BASE}/requirements/${id}/reject`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to reject requirement');
    return res.json();
  },

  async splitRequirement(id: string, items: Array<{ summary: string; description: string; req_type?: string }>) {
    const res = await fetch(`${API_BASE}/requirements/${id}/split`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ split_into: items }),
    });
    if (!res.ok) throw new Error('Failed to split requirement');
    return res.json();
  },

  async mergeRequirements(sourceIds: string[], summary: string, description: string) {
    const res = await fetch(`${API_BASE}/requirements/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_requirement_ids: sourceIds, merged_summary: summary, merged_description: description }),
    });
    if (!res.ok) throw new Error('Failed to merge requirements');
    return res.json();
  },

  // Issues
  async getIssues(projectId: string, issueType?: string, status?: string): Promise<RequirementIssue[]> {
    const params = new URLSearchParams();
    if (issueType) params.append('issue_type', issueType);
    if (status) params.append('status', status);
    const res = await fetch(`${API_BASE}/projects/${projectId}/issues?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to fetch issues');
    return res.json();
  },

  async resolveIssue(id: string, resolutionNote: string) {
    const res = await fetch(`${API_BASE}/issues/${id}/resolve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution_note: resolutionNote }),
    });
    if (!res.ok) throw new Error('Failed to resolve issue');
    return res.json();
  },

  async dismissIssue(id: string) {
    const res = await fetch(`${API_BASE}/issues/${id}/dismiss`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to dismiss issue');
    return res.json();
  },

  // Clarifications
  async getClarifications(projectId: string): Promise<ClarificationQuestion[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/clarifications`);
    if (!res.ok) throw new Error('Failed to fetch clarifications');
    return res.json();
  },

  async answerClarification(id: string, answer: string, updateRequirement: boolean = true) {
    const res = await fetch(`${API_BASE}/clarifications/${id}/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answer, update_requirement: updateRequirement }),
    });
    if (!res.ok) throw new Error('Failed to submit clarification answer');
    return res.json();
  },

  // Architecture
  async getArchitecture(projectId: string): Promise<{ modules: ArchitectureModule[]; relations: ArchitectureRelation[] }> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/architecture`);
    if (!res.ok) throw new Error('Failed to fetch architecture');
    return res.json();
  },

  async generateArchitecture(projectId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/architecture/generate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to generate architecture');
    return res.json();
  },

  async updateModulePosition(id: string, posX: number, posY: number) {
    const res = await fetch(`${API_BASE}/architecture/modules/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pos_x: posX, pos_y: posY }),
    });
    return res.json();
  },

  // Planning & Tasks
  async getTasks(projectId: string): Promise<Task[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/tasks`);
    if (!res.ok) throw new Error('Failed to fetch tasks');
    return res.json();
  },

  async updateTaskStatus(id: string, status: string, assigneeName?: string) {
    const res = await fetch(`${API_BASE}/tasks/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, assignee_name: assigneeName }),
    });
    if (!res.ok) throw new Error('Failed to update task');
    return res.json();
  },

  // Team
  async getTeam(projectId: string): Promise<TeamMember[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/team`);
    if (!res.ok) throw new Error('Failed to fetch team');
    return res.json();
  },

  async autoAssignTeam(projectId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/team/auto-assign`, { method: 'POST' });
    if (!res.ok) throw new Error('Auto-assignment failed');
    return res.json();
  },

  // Traceability
  async getTraceability(projectId: string): Promise<TraceabilityResponse> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/traceability`);
    if (!res.ok) throw new Error('Failed to fetch traceability matrix');
    return res.json();
  },

  // Change Impact
  async simulateChangeImpact(projectId: string, requirementId: string, proposedSummary: string, proposedDescription: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/change-impact/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirement_id: requirementId,
        title: `Change to ${requirementId}`,
        description: 'User initiated simulation',
        proposed_summary: proposedSummary,
        proposed_description: proposedDescription,
      }),
    });
    if (!res.ok) throw new Error('Change impact simulation failed');
    return res.json();
  },

  async applyChangeRequest(projectId: string, requirementId: string, proposedSummary: string, proposedDescription: string): Promise<ChangeRequest> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/change-impact/apply`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        requirement_id: requirementId,
        title: `CR: Update ${requirementId}`,
        description: 'Applied via Change Impact Console',
        proposed_summary: proposedSummary,
        proposed_description: proposedDescription,
      }),
    });
    if (!res.ok) throw new Error('Failed to apply change request');
    return res.json();
  },

  async getChangeRequests(projectId: string): Promise<ChangeRequest[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/change-impact`);
    if (!res.ok) throw new Error('Failed to fetch change requests');
    return res.json();
  },

  // Reports
  async getReports(projectId: string): Promise<ReportItem[]> {
    const res = await fetch(`${API_BASE}/projects/${projectId}/reports`);
    if (!res.ok) throw new Error('Failed to fetch reports');
    return res.json();
  },

  async generateReports(projectId: string) {
    const res = await fetch(`${API_BASE}/projects/${projectId}/reports/generate`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to generate reports');
    return res.json();
  },

  // Evaluation
  async runEvaluation(): Promise<EvaluationResult> {
    const res = await fetch(`${API_BASE}/evaluation/run`);
    if (!res.ok) throw new Error('Failed to run benchmarks');
    return res.json();
  },
};
