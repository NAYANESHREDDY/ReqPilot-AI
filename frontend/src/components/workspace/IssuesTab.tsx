import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { RequirementIssue } from '../../types';
import {
  AlertTriangle, CheckCircle2, XCircle, Search, HelpCircle,
  ArrowRight, ShieldAlert, Check, MessageSquare
} from 'lucide-react';

export const IssuesTab: React.FC = () => {
  const { activeProject, refreshStats, setActiveTab, showToast } = useApp();
  const [issues, setIssues] = useState<RequirementIssue[]>([]);
  const [filterType, setFilterType] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('open');
  const [searchQuery, setSearchQuery] = useState('');

  // Resolve Modal State
  const [resolvingIssue, setResolvingIssue] = useState<RequirementIssue | null>(null);
  const [resolutionNote, setResolutionNote] = useState('');

  const loadIssues = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getIssues(
        activeProject.id,
        filterType === 'all' ? undefined : filterType,
        filterStatus === 'all' ? undefined : filterStatus
      );
      setIssues(data);
    } catch (e) {
      console.error('Error loading issues', e);
    }
  };

  useEffect(() => {
    loadIssues();
  }, [activeProject, filterType, filterStatus]);

  const handleResolve = async () => {
    if (!resolvingIssue) return;
    try {
      await api.resolveIssue(resolvingIssue.id, resolutionNote);
      showToast('Issue marked as resolved!', 'success');
      setResolvingIssue(null);
      setResolutionNote('');
      await loadIssues();
      await refreshStats();
    } catch (e) {
      showToast('Failed to resolve issue', 'error');
    }
  };

  const handleDismiss = async (id: string) => {
    try {
      await api.dismissIssue(id);
      showToast('Issue dismissed.', 'info');
      await loadIssues();
      await refreshStats();
    } catch (e) {
      showToast('Failed to dismiss issue', 'error');
    }
  };

  const filteredIssues = issues.filter((i) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      i.title.toLowerCase().includes(q) ||
      i.description.toLowerCase().includes(q) ||
      (i.requirement_id && i.requirement_id.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search issues by title, phrase, or requirement ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Issue Type Filters */}
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setFilterType('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                filterType === 'all' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Issues
            </button>
            <button
              onClick={() => setFilterType('conflict')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                filterType === 'conflict' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Conflicts
            </button>
            <button
              onClick={() => setFilterType('ambiguity')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                filterType === 'ambiguity' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Ambiguities
            </button>
            <button
              onClick={() => setFilterType('duplicate')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold ${
                filterType === 'duplicate' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Duplicates
            </button>
          </div>

          {/* Status Filter */}
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setFilterStatus('open')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                filterStatus === 'open' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Open
            </button>
            <button
              onClick={() => setFilterStatus('resolved')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                filterStatus === 'resolved' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Resolved
            </button>
            <button
              onClick={() => setFilterStatus('all')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                filterStatus === 'all' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All
            </button>
          </div>
        </div>
      </div>

      {/* Issues List */}
      <div className="space-y-4">
        {filteredIssues.length === 0 ? (
          <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800 text-slate-400 space-y-2">
            <CheckCircle2 className="h-8 w-8 mx-auto text-emerald-400" />
            <p className="text-sm font-semibold">No issues found in this category.</p>
            <p className="text-xs text-slate-500">All ambiguity, conflict, and duplicate requirements are verified.</p>
          </div>
        ) : (
          filteredIssues.map((issue) => (
            <div
              key={issue.id}
              className={`glass-panel rounded-2xl border transition-all p-5 space-y-3 ${
                issue.status === 'resolved'
                  ? 'border-emerald-800/40 bg-slate-900/40 opacity-75'
                  : issue.severity === 'high' || issue.severity === 'critical'
                  ? 'border-red-900/40 bg-gradient-to-r from-red-950/20 via-slate-900 to-slate-900'
                  : 'border-slate-800'
              }`}
            >
              {/* Top Row: Type & Severity Badges */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                      issue.issue_type === 'conflict'
                        ? 'bg-red-950/80 border-red-800/80 text-red-300'
                        : issue.issue_type === 'ambiguity'
                        ? 'bg-amber-950/80 border-amber-800/80 text-amber-300'
                        : 'bg-blue-950/80 border-blue-800/80 text-blue-300'
                    }`}
                  >
                    {issue.issue_type}
                  </span>

                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                      issue.severity === 'high' || issue.severity === 'critical'
                        ? 'bg-red-900/60 border-red-700/60 text-red-200'
                        : 'bg-slate-800 border-slate-700 text-slate-300'
                    }`}
                  >
                    {issue.severity} Severity
                  </span>

                  {issue.requirement_id && (
                    <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950/60 border border-indigo-800/60 px-2 py-0.5 rounded-lg">
                      Target: {issue.requirement_id}
                    </span>
                  )}

                  {issue.conflict_with_id && (
                    <span className="font-mono text-xs font-bold text-red-300 bg-red-950/60 border border-red-800/60 px-2 py-0.5 rounded-lg">
                      Conflicts With: {issue.conflict_with_id}
                    </span>
                  )}

                  <span className="text-[10px] text-slate-400">
                    Confidence: {Math.round(issue.confidence * 100)}%
                  </span>
                </div>

                {/* Resolve / Dismiss buttons */}
                {issue.status === 'open' && (
                  <div className="flex items-center space-x-2 shrink-0">
                    <button
                      onClick={() => {
                        setResolvingIssue(issue);
                        setResolutionNote(`Resolved conflict between specifications.`);
                      }}
                      className="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-600/40 px-3 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
                    >
                      <Check className="h-3.5 w-3.5" />
                      <span>Resolve</span>
                    </button>
                    <button
                      onClick={() => handleDismiss(issue.id)}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-400 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all"
                    >
                      Dismiss
                    </button>
                  </div>
                )}
              </div>

              {/* Title & Description */}
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-white">{issue.title}</h3>
                <p className="text-xs text-slate-300 leading-relaxed">{issue.description}</p>
              </div>

              {/* Highlight Box */}
              {issue.detected_phrase && (
                <div className="bg-slate-950/80 border border-slate-800 p-2.5 rounded-xl flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="text-slate-500 font-semibold">Detected phrase:</span>
                    <span className="font-mono text-amber-300 bg-amber-950/60 border border-amber-800/60 px-2 py-0.5 rounded">
                      "{issue.detected_phrase}"
                    </span>
                  </div>

                  {issue.issue_type === 'ambiguity' && (
                    <button
                      onClick={() => setActiveTab('clarifications')}
                      className="text-indigo-400 hover:text-indigo-300 font-semibold text-[11px] flex items-center space-x-1"
                    >
                      <span>Go to Clarifications</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  )}
                </div>
              )}

              {/* Resolved Note */}
              {issue.status === 'resolved' && (
                <div className="text-[11px] text-emerald-400 bg-emerald-950/40 border border-emerald-900/40 p-2 rounded-lg flex items-center space-x-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
                  <span>Resolution Note: {issue.resolution_note || 'Resolved by Analyst'}</span>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Resolve Modal */}
      {resolvingIssue && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Resolve Issue: {resolvingIssue.title}</h3>
            <p className="text-xs text-slate-400">
              Provide an engineering resolution note or architectural baseline decision.
            </p>

            <textarea
              rows={3}
              value={resolutionNote}
              onChange={(e) => setResolutionNote(e.target.value)}
              placeholder="e.g. Stakeholders agreed on 2-hour tiered cancellation policy in sprint grooming."
              className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            />

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setResolvingIssue(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleResolve}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-500 shadow-md shadow-emerald-600/30"
              >
                Confirm Resolution
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
