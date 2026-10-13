import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { ReportItem } from '../../types';
import {
  BookOpen, Printer, Copy, Check, RefreshCw, FileText,
  ShieldAlert, Layers, Calendar, GitMerge, Zap
} from 'lucide-react';

export const ReportsTab: React.FC = () => {
  const { activeProject, showToast } = useApp();
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [activeReportType, setActiveReportType] = useState<string>('srs');
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const loadReports = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getReports(activeProject.id);
      setReports(data);
    } catch (e) {
      console.error('Failed to load reports', e);
    }
  };

  useEffect(() => {
    loadReports();
  }, [activeProject]);

  const handleRegenerate = async () => {
    if (!activeProject) return;
    setIsGenerating(true);
    try {
      await api.generateReports(activeProject.id);
      showToast('All 6 formal engineering reports regenerated!', 'success');
      await loadReports();
    } catch (e) {
      showToast('Report generation failed', 'error');
    } finally {
      setIsGenerating(false);
    }
  };

  const currentReport = reports.find((r) => r.report_type === activeReportType) || reports[0];

  const handleCopy = () => {
    if (!currentReport) return;
    navigator.clipboard.writeText(currentReport.content_markdown);
    setCopied(true);
    showToast('Report markdown copied to clipboard!', 'success');
    setTimeout(() => setCopied(false), 2500);
  };

  const handlePrint = () => {
    window.print();
  };

  const reportTabs = [
    { id: 'srs', title: '1. SRS Specification', icon: FileText },
    { id: 'quality_audit', title: '2. Quality & Risk Audit', icon: ShieldAlert },
    { id: 'architecture', title: '3. Architecture Proposal', icon: Layers },
    { id: 'plan', title: '4. Project Plan & Sprints', icon: Calendar },
    { id: 'traceability', title: '5. Traceability Matrix', icon: GitMerge },
    { id: 'change_impact', title: '6. Change Impact Audit', icon: Zap },
  ];

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Engineering Reports & Artifacts (Section 31)</h3>
            <p className="text-xs text-slate-400">
              Publication-ready formal deliverables with complete provenance citations, quality audits, and schedules.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopy}
            disabled={!currentReport}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            <span>{copied ? 'Copied' : 'Copy Markdown'}</span>
          </button>

          <button
            onClick={handlePrint}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <Printer className="h-3.5 w-3.5" />
            <span>Print / Export</span>
          </button>

          <button
            onClick={handleRegenerate}
            disabled={isGenerating}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isGenerating ? 'animate-spin' : ''}`} />
            <span>{isGenerating ? 'Compiling...' : 'Regenerate'}</span>
          </button>
        </div>
      </div>

      {/* Main Report Container */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Col: 6 Report Selectors */}
        <div className="glass-panel p-3 rounded-2xl border border-slate-800 space-y-1">
          <span className="text-[10px] uppercase font-bold text-slate-500 px-3 py-1 block">
            Deliverable Reports
          </span>
          {reportTabs.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeReportType === tab.id;

            return (
              <button
                key={tab.id}
                onClick={() => setActiveReportType(tab.id)}
                className={`w-full text-left p-3 rounded-xl text-xs font-semibold flex items-center space-x-2.5 transition-all ${
                  isSelected
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/25'
                    : 'text-slate-300 hover:bg-slate-800/80 hover:text-white'
                }`}
              >
                <Icon className={`h-4 w-4 ${isSelected ? 'text-white' : 'text-slate-400'}`} />
                <span className="truncate">{tab.title}</span>
              </button>
            );
          })}
        </div>

        {/* Right 3 Cols: Report Viewer */}
        <div className="lg:col-span-3 glass-panel p-8 rounded-2xl border border-slate-800 space-y-6 print:p-0 print:border-none">
          {!currentReport ? (
            <div className="text-center py-20 text-xs text-slate-500">
              No report compiled yet. Click "Regenerate" to build all reports.
            </div>
          ) : (
            <div className="space-y-4">
              <div className="border-b border-slate-800 pb-4 flex items-center justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-400">
                    Formal Project Document
                  </span>
                  <h2 className="text-xl font-bold text-white mt-0.5">{currentReport.title}</h2>
                </div>
                <span className="text-[11px] text-slate-500">
                  {new Date(currentReport.created_at).toLocaleDateString()}
                </span>
              </div>

              {/* Rendered Markdown Body */}
              <div className="prose prose-invert max-w-none text-slate-200 text-xs leading-relaxed font-mono whitespace-pre-wrap bg-slate-950/80 p-6 rounded-xl border border-slate-800">
                {currentReport.content_markdown}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
