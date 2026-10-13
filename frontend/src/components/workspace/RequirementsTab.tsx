import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { Requirement } from '../../types';
import {
  Check, X, Edit3, Split, Search, Filter, Quote, Plus, CheckCircle2,
  AlertCircle, Shield, Award, Sparkles, ChevronDown, ChevronUp
} from 'lucide-react';

export const RequirementsTab: React.FC = () => {
  const { activeProject, refreshStats, showToast } = useApp();
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [filteredReqs, setFilteredReqs] = useState<Requirement[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'all' | 'functional' | 'non_functional'>('all');
  const [statusFilter, setStatusFilter] = useState<'all' | 'approved' | 'needs_review' | 'rejected'>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Edit Modal State
  const [editingReq, setEditingReq] = useState<Requirement | null>(null);
  const [editSummary, setEditSummary] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editPriority, setEditPriority] = useState<string>('medium');

  // Split Modal State
  const [splittingReq, setSplittingReq] = useState<Requirement | null>(null);
  const [splitPart1, setSplitPart1] = useState('');
  const [splitPart2, setSplitPart2] = useState('');

  const loadRequirements = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getRequirements(activeProject.id);
      setRequirements(data);
    } catch (e) {
      console.error('Error loading requirements', e);
    }
  };

  useEffect(() => {
    loadRequirements();
  }, [activeProject]);

  useEffect(() => {
    let list = requirements;
    if (typeFilter !== 'all') {
      list = list.filter((r) => r.req_type === typeFilter);
    }
    if (statusFilter !== 'all') {
      list = list.filter((r) => r.status === statusFilter);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      list = list.filter(
        (r) =>
          r.id.toLowerCase().includes(q) ||
          r.summary.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q) ||
          r.actor.toLowerCase().includes(q)
      );
    }
    setFilteredReqs(list);
  }, [requirements, typeFilter, statusFilter, searchQuery]);

  const handleApprove = async (id: string) => {
    try {
      await api.approveRequirement(id);
      showToast(`Requirement ${id} approved!`, 'success');
      await loadRequirements();
      await refreshStats();
    } catch (e) {
      showToast('Approval failed', 'error');
    }
  };

  const handleReject = async (id: string) => {
    try {
      await api.rejectRequirement(id);
      showToast(`Requirement ${id} rejected.`, 'info');
      await loadRequirements();
      await refreshStats();
    } catch (e) {
      showToast('Rejection failed', 'error');
    }
  };

  const openEditModal = (req: Requirement) => {
    setEditingReq(req);
    setEditSummary(req.summary);
    setEditDescription(req.description);
    setEditPriority(req.priority);
  };

  const saveEdit = async () => {
    if (!editingReq) return;
    try {
      await api.updateRequirement(editingReq.id, {
        summary: editSummary,
        description: editDescription,
        priority: editPriority as any,
      });
      showToast(`Requirement ${editingReq.id} updated!`, 'success');
      setEditingReq(null);
      await loadRequirements();
    } catch (e) {
      showToast('Failed to save update', 'error');
    }
  };

  const openSplitModal = (req: Requirement) => {
    setSplittingReq(req);
    setSplitPart1(req.summary);
    setSplitPart2('Secondary related requirement statement');
  };

  const executeSplit = async () => {
    if (!splittingReq) return;
    try {
      await api.splitRequirement(splittingReq.id, [
        { summary: splitPart1, description: splitPart1, req_type: splittingReq.req_type },
        { summary: splitPart2, description: splitPart2, req_type: splittingReq.req_type },
      ]);
      showToast(`Requirement ${splittingReq.id} split into sub-requirements!`, 'success');
      setSplittingReq(null);
      await loadRequirements();
      await refreshStats();
    } catch (e) {
      showToast('Split failed', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Controls Bar: Search & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-4 rounded-2xl border border-slate-800">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by ID, summary, actor, or criteria..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Type Filter */}
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setTypeFilter('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                typeFilter === 'all' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Types
            </button>
            <button
              onClick={() => setTypeFilter('functional')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                typeFilter === 'functional' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Functional
            </button>
            <button
              onClick={() => setTypeFilter('non_functional')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all ${
                typeFilter === 'non_functional' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              NFR
            </button>
          </div>

          {/* Status Filter */}
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                statusFilter === 'all' ? 'bg-slate-700 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              All Status
            </button>
            <button
              onClick={() => setStatusFilter('needs_review')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                statusFilter === 'needs_review' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Needs Review
            </button>
            <button
              onClick={() => setStatusFilter('approved')}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${
                statusFilter === 'approved' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'
              }`}
            >
              Approved
            </button>
          </div>
        </div>
      </div>

      {/* Requirements Card List */}
      <div className="space-y-4">
        {filteredReqs.length === 0 ? (
          <div className="glass-panel p-12 text-center rounded-2xl border border-slate-800 text-slate-400 space-y-2">
            <Shield className="h-8 w-8 mx-auto text-slate-500" />
            <p className="text-sm font-semibold">No requirements match your current filter.</p>
            <p className="text-xs text-slate-500">Click "Analyze Requirements" on top to extract structured items from your sources.</p>
          </div>
        ) : (
          filteredReqs.map((req) => {
            const isExpanded = expandedId === req.id;

            return (
              <div
                key={req.id}
                className="glass-panel rounded-2xl border border-slate-800 hover:border-slate-700 transition-all p-5 space-y-4"
              >
                {/* Top Row: Badges & Human Actions */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-2.5 flex-wrap gap-y-1">
                    <span className="font-mono text-xs font-bold text-white bg-slate-800/90 border border-slate-700 px-2.5 py-1 rounded-lg">
                      {req.id}
                    </span>

                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        req.req_type === 'functional'
                          ? 'bg-blue-950/70 border-blue-800/70 text-blue-300'
                          : 'bg-purple-950/70 border-purple-800/70 text-purple-300'
                      }`}
                    >
                      {req.req_type === 'functional' ? 'Functional' : 'Non-Functional'}
                    </span>

                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        req.priority === 'critical'
                          ? 'bg-red-950/70 border-red-800/70 text-red-300'
                          : req.priority === 'high'
                          ? 'bg-orange-950/70 border-orange-800/70 text-orange-300'
                          : 'bg-slate-800 border-slate-700 text-slate-300'
                      }`}
                    >
                      {req.priority} Priority
                    </span>

                    {/* Quality Score Badge */}
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 flex items-center space-x-1">
                      <Award className="h-3 w-3 mr-0.5" />
                      Quality: {req.quality_score}%
                    </span>

                    {/* Status Badge */}
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        req.status === 'approved'
                          ? 'bg-emerald-950/80 border-emerald-800/80 text-emerald-300'
                          : req.status === 'rejected'
                          ? 'bg-red-950/80 border-red-800/80 text-red-400'
                          : 'bg-amber-950/80 border-amber-800/80 text-amber-300'
                      }`}
                    >
                      {req.status === 'needs_review' ? 'Needs Review' : req.status}
                    </span>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex items-center space-x-2 shrink-0">
                    {req.status !== 'approved' && (
                      <button
                        onClick={() => handleApprove(req.id)}
                        className="bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-300 border border-emerald-600/40 px-2.5 py-1 rounded-lg text-xs font-semibold flex items-center space-x-1 transition-all"
                        title="Approve Requirement"
                      >
                        <Check className="h-3.5 w-3.5" />
                        <span>Approve</span>
                      </button>
                    )}

                    {req.status !== 'rejected' && (
                      <button
                        onClick={() => handleReject(req.id)}
                        className="bg-red-600/10 hover:bg-red-600/20 text-red-400 border border-red-600/30 px-2 py-1 rounded-lg text-xs font-semibold transition-all"
                        title="Reject Requirement"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    )}

                    <button
                      onClick={() => openEditModal(req)}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded-lg text-xs font-semibold transition-all"
                      title="Edit Requirement"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>

                    <button
                      onClick={() => openSplitModal(req)}
                      className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-2 py-1 rounded-lg text-xs font-semibold transition-all"
                      title="Split into Sub-Requirements"
                    >
                      <Split className="h-3.5 w-3.5" />
                    </button>

                    <button
                      onClick={() => setExpandedId(isExpanded ? null : req.id)}
                      className="text-slate-400 hover:text-slate-200 p-1"
                      title="Toggle Details"
                    >
                      {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                {/* Summary & Statement */}
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-white tracking-tight">{req.summary}</h3>
                  <p className="text-xs text-slate-300 leading-relaxed">{req.description}</p>
                </div>

                {/* Source Grounding Provenance Box (Section 22 Hallucination Control) */}
                <div className="bg-slate-900/90 border border-slate-800 p-3 rounded-xl flex items-start space-x-3 text-xs">
                  <Quote className="h-4 w-4 text-indigo-400 shrink-0 mt-0.5" />
                  <div className="space-y-0.5 overflow-hidden">
                    <div className="flex items-center space-x-2 text-[11px] font-semibold text-indigo-300">
                      <span>Source Evidence:</span>
                      <span className="text-slate-400">{req.source_id} (Page {req.source_page})</span>
                    </div>
                    <p className="text-slate-400 italic truncate max-w-2xl">
                      "{req.source_excerpt}"
                    </p>
                  </div>
                </div>

                {/* Expanded Details: Actor, Action, Acceptance Criteria */}
                {isExpanded && (
                  <div className="pt-3 border-t border-slate-800/80 space-y-3 text-xs animate-in fade-in slide-in-from-top-1">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                      <div>
                        <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Actor</span>
                        <span className="font-semibold text-slate-200">{req.actor}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Action</span>
                        <span className="font-semibold text-slate-200">{req.action || 'Execute'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Target Object</span>
                        <span className="font-semibold text-slate-200">{req.target_object || 'System'}</span>
                      </div>
                      <div>
                        <span className="text-slate-500 uppercase tracking-wider text-[10px] block">Version</span>
                        <span className="font-semibold text-indigo-400">v{req.version}.0</span>
                      </div>
                    </div>

                    {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
                      <div className="space-y-1">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                          Acceptance Criteria
                        </span>
                        <ul className="list-disc list-inside space-y-1 text-slate-300 pl-1">
                          {req.acceptance_criteria.map((c, idx) => (
                            <li key={idx} className="leading-relaxed">{c}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Edit Modal */}
      {editingReq && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Edit Requirement {editingReq.id}</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Summary Title</label>
                <input
                  type="text"
                  value={editSummary}
                  onChange={(e) => setEditSummary(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Requirement Statement</label>
                <textarea
                  rows={3}
                  value={editDescription}
                  onChange={(e) => setEditDescription(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Priority</label>
                <select
                  value={editPriority}
                  onChange={(e) => setEditPriority(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="low">Low Priority</option>
                  <option value="medium">Medium Priority</option>
                  <option value="high">High Priority</option>
                  <option value="critical">Critical Priority</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setEditingReq(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={saveEdit}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
              >
                Save Changes
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Split Modal */}
      {splittingReq && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div>
              <h3 className="text-base font-bold text-white">Split Requirement {splittingReq.id}</h3>
              <p className="text-xs text-slate-400 mt-1">Decompose this requirement into 2 atomic specifications.</p>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Part 1 ({splittingReq.id}.1)</label>
                <input
                  type="text"
                  value={splitPart1}
                  onChange={(e) => setSplitPart1(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Part 2 ({splittingReq.id}.2)</label>
                <input
                  type="text"
                  value={splitPart2}
                  onChange={(e) => setSplitPart2(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setSplittingReq(null)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={executeSplit}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
              >
                Confirm Split
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
