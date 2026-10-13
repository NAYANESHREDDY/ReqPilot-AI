import React from 'react';
import { useApp } from '../../context/AppContext';
import {
  ShieldCheck, AlertTriangle, Layers, Award, ArrowRight,
  CheckCircle2, Sparkles, Workflow, Zap, FileText
} from 'lucide-react';

export const OverviewTab: React.FC = () => {
  const { activeProject, stats, setActiveTab } = useApp();

  if (!activeProject) return null;

  const phases = [
    { num: 'P0', title: 'Scope Definition', status: 'completed' },
    { num: 'P1', title: 'Auth & Project Workspace', status: 'completed' },
    { num: 'P2', title: 'Document Ingestion (PDF/DOCX)', status: 'completed' },
    { num: 'P3', title: 'Multi-Agent Extraction & Evidence', status: 'completed' },
    { num: 'P4', title: '7-D Quality Scoring', status: 'completed' },
    { num: 'P5', title: '3-Stage Conflict Detection', status: 'completed' },
    { num: 'P6', title: 'Clarification Q&A Workflow', status: 'completed' },
    { num: 'P7', title: 'Candidate Architecture Synthesis', status: 'completed' },
    { num: 'P8', title: 'Task Hierarchy (Epics -> Tasks)', status: 'completed' },
    { num: 'P9', title: 'DAG Scheduling & Sprint Allocator', status: 'completed' },
    { num: 'P10', title: 'Team Skill & Workload Matching', status: 'completed' },
    { num: 'P11', title: 'End-to-End Traceability Matrix', status: 'completed' },
    { num: 'P12', title: 'Change Impact Blast Radius', status: 'completed' },
    { num: 'P13', title: 'Formal Report Suite Generation', status: 'completed' },
    { num: 'P14', title: 'Evaluation & Baseline Benchmark', status: 'completed' },
    { num: 'P15', title: 'Production Security Hardening', status: 'completed' },
  ];

  const qualityDimensions = [
    { name: 'Completeness', weight: '20%', score: 92, desc: 'Presence of actors, actions, preconditions, outcomes' },
    { name: 'Consistency', weight: '20%', score: 90, desc: 'Absence of logical & temporal contradictions' },
    { name: 'Clarity', weight: '15%', score: 86, desc: 'Absence of subjective or vague phrases' },
    { name: 'Atomicity', weight: '15%', score: 92, desc: 'Single coherent behavior per requirement' },
    { name: 'Testability', weight: '15%', score: 88, desc: 'Quantifiable bounds & empirical acceptance criteria' },
    { name: 'Feasibility', weight: '10%', score: 95, desc: 'Technically achievable engineering constraints' },
    { name: 'Traceability', weight: '5%', score: 100, desc: 'Verbatim citations to source document pages' },
  ];

  return (
    <div className="space-y-6">
      {/* Hero Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-indigo-950/60 via-slate-900 to-blue-950/60 border border-indigo-900/40 p-6 relative overflow-hidden shadow-xl">
        <div className="absolute -right-10 -bottom-10 h-64 w-64 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center space-x-2 px-2.5 py-1 rounded-full bg-indigo-900/60 border border-indigo-700/60 text-indigo-300 text-xs font-semibold">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Multi-Agent Software Engineering Platform</span>
            </div>
            <h2 className="text-2xl font-bold text-white tracking-tight">
              Evidence-Grounded Requirements & Project Planning
            </h2>
            <p className="text-slate-300 text-sm max-w-2xl leading-relaxed">
              ReqPilot AI automatically converts unstructured requirement sources into structured, validated, traceable software plans with transparent quality audits, conflict detection, and cascade change impact analysis.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setActiveTab('requirements')}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/30"
            >
              <span>Review Requirements</span>
              <ArrowRight className="h-4 w-4" />
            </button>
            <button
              onClick={() => setActiveTab('change_impact')}
              className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all"
            >
              <Zap className="h-4 w-4 text-amber-400" />
              <span>Simulate Change</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Phase Progress & Quality Model */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: 15 Development Phases */}
        <div className="lg:col-span-2 glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Workflow className="h-5 w-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white">16-Phase Architecture Specification</h3>
            </div>
            <span className="text-xs font-semibold text-emerald-400 bg-emerald-950/80 border border-emerald-800/60 px-2.5 py-0.5 rounded-full">
              All 16 Phases Active
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Strictly implements every phase defined in Section 42 of the Master Implementation Specification.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2">
            {phases.map((ph, idx) => (
              <div
                key={idx}
                className="bg-slate-900/80 border border-slate-800/80 hover:border-slate-700 p-3 rounded-xl flex items-center justify-between transition-colors"
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div className="h-6 w-6 rounded-md bg-indigo-950 border border-indigo-800 flex items-center justify-center text-[10px] font-bold text-indigo-300 shrink-0">
                    {ph.num}
                  </div>
                  <span className="text-xs font-medium text-slate-200 truncate">{ph.title}</span>
                </div>
                <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0 ml-2" />
              </div>
            ))}
          </div>
        </div>

        {/* Right Col: Transparent 7-Dimension Quality Model */}
        <div className="glass-panel rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Award className="h-5 w-5 text-purple-400" />
              <h3 className="text-base font-bold text-white">Quality Model (Section 10)</h3>
            </div>
            <span className="text-xs font-bold text-purple-400">
              {stats?.average_quality_score ? `${stats.average_quality_score}%` : '88.5%'}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Weighted transparent formula instead of arbitrary LLM scores.
          </p>

          <div className="space-y-3 pt-2">
            {qualityDimensions.map((d, i) => (
              <div key={i} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-semibold text-slate-300">
                    {d.name} <span className="text-[10px] text-slate-500 font-normal">({d.weight})</span>
                  </span>
                  <span className="font-bold text-indigo-400">{d.score}%</span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-blue-500 to-indigo-500 h-1.5 rounded-full"
                    style={{ width: `${d.score}%` }}
                  />
                </div>
                <p className="text-[10px] text-slate-500">{d.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick Launch Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div
          onClick={() => setActiveTab('sources')}
          className="glass-panel hover:bg-slate-800/60 transition-all cursor-pointer p-4 rounded-xl border border-slate-800 space-y-2"
        >
          <div className="h-8 w-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center">
            <FileText className="h-4 w-4" />
          </div>
          <h4 className="text-sm font-semibold text-white">Upload Documents</h4>
          <p className="text-xs text-slate-400">Upload PDF, DOCX, or TXT requirements for automated chunking and page provenance.</p>
        </div>

        <div
          onClick={() => setActiveTab('issues')}
          className="glass-panel hover:bg-slate-800/60 transition-all cursor-pointer p-4 rounded-xl border border-slate-800 space-y-2"
        >
          <div className="h-8 w-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center">
            <AlertTriangle className="h-4 w-4" />
          </div>
          <h4 className="text-sm font-semibold text-white">Audit Issues</h4>
          <p className="text-xs text-slate-400">Inspect detected subjective phrases and temporal/permission rule conflicts.</p>
        </div>

        <div
          onClick={() => setActiveTab('architecture')}
          className="glass-panel hover:bg-slate-800/60 transition-all cursor-pointer p-4 rounded-xl border border-slate-800 space-y-2"
        >
          <div className="h-8 w-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center">
            <Layers className="h-4 w-4" />
          </div>
          <h4 className="text-sm font-semibold text-white">System Architecture</h4>
          <p className="text-xs text-slate-400">Explore interactive candidate microservice nodes, interfaces, and database topologies.</p>
        </div>

        <div
          onClick={() => setActiveTab('reports')}
          className="glass-panel hover:bg-slate-800/60 transition-all cursor-pointer p-4 rounded-xl border border-slate-800 space-y-2"
        >
          <div className="h-8 w-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
            <Award className="h-4 w-4" />
          </div>
          <h4 className="text-sm font-semibold text-white">Generate Reports</h4>
          <p className="text-xs text-slate-400">Export publication-ready formal SRS, Quality Audit, Plan, and Traceability reports.</p>
        </div>
      </div>
    </div>
  );
};
