import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { Requirement, ChangeRequest } from '../../types';
import {
  Zap, AlertTriangle, CheckCircle2, Clock, ArrowRight, ShieldAlert,
  Calendar, Layers, CheckSquare, ShieldCheck, Sparkles, RefreshCw
} from 'lucide-react';

export const ChangeImpactTab: React.FC = () => {
  const { activeProject, refreshStats, showToast } = useApp();
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [selectedReqId, setSelectedReqId] = useState<string>('');
  const [proposedSummary, setProposedSummary] = useState('');
  const [proposedDesc, setProposedDesc] = useState('');
  const [simulation, setSimulation] = useState<any | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [pastChangeRequests, setPastChangeRequests] = useState<ChangeRequest[]>([]);

  const loadData = async () => {
    if (!activeProject) return;
    try {
      const [reqData, crData] = await Promise.all([
        api.getRequirements(activeProject.id),
        api.getChangeRequests(activeProject.id),
      ]);
      setRequirements(reqData);
      setPastChangeRequests(crData);

      if (reqData.length > 0 && !selectedReqId) {
        // Default to FR-006 (the cancellation policy requirement) or first req
        const cancelReq = reqData.find((r) => r.id === 'FR-006') || reqData[0];
        setSelectedReqId(cancelReq.id);
        setProposedSummary('Students may cancel bookings up to 2 hours before the session with partial refund.');
        setProposedDesc('Students can cancel up to 2 hours prior with 50% refund. Cancellations under 2 hours forfeit full fee.');
      }
    } catch (e) {
      console.error('Error loading change impact data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeProject]);

  const handleSelectReq = (reqId: string) => {
    setSelectedReqId(reqId);
    const found = requirements.find((r) => r.id === reqId);
    if (found) {
      setProposedSummary(`${found.summary} (Modified Policy)`);
      setProposedDesc(`Revised specification for ${found.summary} with updated business constraints.`);
    }
    setSimulation(null);
  };

  const handleSimulate = async () => {
    if (!activeProject || !selectedReqId || !proposedSummary.trim()) return;
    setIsSimulating(true);
    try {
      const res = await api.simulateChangeImpact(activeProject.id, selectedReqId, proposedSummary, proposedDesc);
      setSimulation(res);
      showToast('Blast radius simulation completed!', 'success');
    } catch (e) {
      showToast('Simulation failed', 'error');
    } finally {
      setIsSimulating(false);
    }
  };

  const handleApplyChange = async () => {
    if (!activeProject || !selectedReqId || !proposedSummary.trim()) return;
    setIsApplying(true);
    try {
      const cr = await api.applyChangeRequest(activeProject.id, selectedReqId, proposedSummary, proposedDesc);
      showToast(`Change Request ${cr.id} approved & applied! Requirement baseline incremented.`, 'success');
      await loadData();
      await refreshStats();
      setSimulation(null);
    } catch (e) {
      showToast('Failed to apply change request', 'error');
    } finally {
      setIsApplying(false);
    }
  };

  const currentReq = requirements.find((r) => r.id === selectedReqId);

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-amber-950/50 via-slate-900 to-indigo-950/50 border border-amber-800/40 p-5 space-y-2">
        <div className="flex items-center space-x-2">
          <div className="h-7 w-7 rounded-lg bg-amber-500/20 border border-amber-500/40 flex items-center justify-center text-amber-400 font-bold">
            <Zap className="h-4 w-4" />
          </div>
          <h3 className="text-base font-bold text-white">
            Requirements Change Impact & Blast Radius Simulator (Section 15 & 30)
          </h3>
        </div>
        <p className="text-xs text-slate-300 max-w-3xl leading-relaxed">
          The killer differentiator: when client stakeholders alter a requirement, ReqPilot AI traverses the dependency graph to immediately compute the cascading blast radius across requirements, microservice modules, tasks, test suites, and schedule shifts.
        </p>
      </div>

      {/* Simulator Inputs & Selection */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Col: Target Requirement Selection & Revision Form */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <h4 className="text-sm font-bold text-white flex items-center space-x-2">
            <RefreshCw className="h-4 w-4 text-indigo-400" />
            <span>1. Select Requirement to Modify</span>
          </h4>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Requirement Target</label>
              <select
                value={selectedReqId}
                onChange={(e) => handleSelectReq(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2 text-white focus:outline-none focus:border-indigo-500"
              >
                {requirements.map((r) => (
                  <option key={r.id} value={r.id}>
                    [{r.id}] {r.summary}
                  </option>
                ))}
              </select>
            </div>

            {currentReq && (
              <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 space-y-1">
                <span className="text-[10px] uppercase font-bold text-slate-500">Current Baseline</span>
                <p className="text-xs font-semibold text-slate-200">{currentReq.summary}</p>
                <p className="text-[11px] text-slate-400 italic">"{currentReq.description}"</p>
              </div>
            )}

            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Proposed Revised Title</label>
              <input
                type="text"
                value={proposedSummary}
                onChange={(e) => setProposedSummary(e.target.value)}
                placeholder="Enter new requirement summary..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-slate-400 mb-1 font-semibold">Proposed Revised Statement</label>
              <textarea
                rows={3}
                value={proposedDesc}
                onChange={(e) => setProposedDesc(e.target.value)}
                placeholder="Enter detailed revised specification..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-white focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              onClick={handleSimulate}
              disabled={isSimulating}
              className="w-full bg-gradient-to-r from-amber-600 to-indigo-600 hover:from-amber-500 hover:to-indigo-500 text-white py-2.5 rounded-xl text-xs font-bold transition-all shadow-md shadow-amber-600/25 flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              <span>{isSimulating ? 'Simulating Blast Radius...' : 'Run Blast Radius Simulation'}</span>
            </button>
          </div>
        </div>

        {/* Right 2 Cols: Simulation Blast Radius Results */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h4 className="text-sm font-bold text-white flex items-center space-x-2">
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              <span>2. Cascade Blast Radius Analysis</span>
            </h4>
            {simulation && (
              <span
                className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border ${
                  simulation.risk_level === 'critical'
                    ? 'bg-red-950 border-red-800 text-red-300'
                    : simulation.risk_level === 'high'
                    ? 'bg-orange-950 border-orange-800 text-orange-300'
                    : 'bg-amber-950 border-amber-800 text-amber-300'
                }`}
              >
                {simulation.risk_level} Risk Level
              </span>
            )}
          </div>

          {!simulation ? (
            <div className="text-center py-16 text-xs text-slate-500 space-y-2">
              <Zap className="h-8 w-8 mx-auto text-slate-600" />
              <p className="font-semibold">No simulation running.</p>
              <p>Select a requirement and click "Run Blast Radius Simulation" to inspect affected modules, tasks, and schedule delay.</p>
            </div>
          ) : (
            <div className="space-y-4 animate-in fade-in slide-in-from-top-2">
              {/* Stat Counters */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 font-semibold block">Affected Tasks</span>
                  <span className="text-lg font-bold text-white">{simulation.summary_stats?.affected_tasks || 0}</span>
                </div>
                <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 font-semibold block">Affected Modules</span>
                  <span className="text-lg font-bold text-emerald-400">{simulation.summary_stats?.affected_modules || 0}</span>
                </div>
                <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 font-semibold block">Affected Tests</span>
                  <span className="text-lg font-bold text-purple-400">{simulation.summary_stats?.affected_tests || 0}</span>
                </div>
                <div className="bg-slate-900/90 p-3 rounded-xl border border-slate-800 text-center">
                  <span className="text-[10px] text-slate-400 font-semibold block">Schedule Shift</span>
                  <span className="text-xs font-bold text-amber-400 mt-1 block">{simulation.schedule_impact}</span>
                </div>
              </div>

              {/* Impact Items Table */}
              <div className="space-y-2">
                <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
                  Impacted Artifacts ({simulation.impact_items?.length || 0})
                </h5>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1 text-xs">
                  {simulation.impact_items?.map((item: any, i: number) => (
                    <div
                      key={i}
                      className="bg-slate-900/80 border border-slate-800/80 p-3 rounded-xl flex items-center justify-between"
                    >
                      <div className="space-y-0.5 max-w-lg">
                        <div className="flex items-center space-x-2">
                          <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 rounded bg-slate-800 text-indigo-300 font-mono">
                            {item.artifact_type}
                          </span>
                          <span className="font-mono text-xs font-bold text-white">{item.artifact_id}</span>
                          <span className="font-semibold text-slate-200">{item.artifact_name}</span>
                        </div>
                        <p className="text-[11px] text-slate-400">{item.impact_description}</p>
                      </div>

                      <span
                        className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border shrink-0 ${
                          item.severity === 'high'
                            ? 'bg-red-950 text-red-300 border-red-800'
                            : 'bg-slate-800 text-slate-300 border-slate-700'
                        }`}
                      >
                        {item.severity}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Approve & Apply Change Gate */}
              <div className="pt-3 border-t border-slate-800 flex items-center justify-between">
                <span className="text-xs text-slate-400">
                  Human Approval Gate: Applying this change will increment the requirement version and log an audit trail.
                </span>
                <button
                  onClick={handleApplyChange}
                  disabled={isApplying}
                  className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 transition-all shadow-md shadow-emerald-600/30 shrink-0 ml-4 disabled:opacity-50"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  <span>{isApplying ? 'Applying...' : 'Approve & Apply Change Request'}</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Past Change Requests History */}
      {pastChangeRequests.length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <h4 className="text-sm font-bold text-white flex items-center space-x-2">
            <Clock className="h-4 w-4 text-indigo-400" />
            <span>Change Request History & Audit Ledger ({pastChangeRequests.length})</span>
          </h4>

          <div className="space-y-3">
            {pastChangeRequests.map((cr) => (
              <div
                key={cr.id}
                className="bg-slate-900/80 border border-slate-800 p-4 rounded-xl space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-amber-400 bg-amber-950/60 border border-amber-800/60 px-2 py-0.5 rounded">
                      {cr.id}
                    </span>
                    <span className="font-bold text-white">{cr.title}</span>
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    {cr.status}
                  </span>
                </div>

                <div className="text-slate-300">
                  <span className="text-slate-500 font-semibold mr-1">Proposed Update:</span>
                  <span>{cr.proposed_summary}</span>
                </div>

                <div className="flex items-center space-x-4 text-[11px] text-slate-500 pt-1">
                  <span>Target: {cr.requirement_id}</span>
                  <span>•</span>
                  <span>Schedule Impact: {cr.schedule_impact}</span>
                  <span>•</span>
                  <span>Risk: {cr.risk_level.toUpperCase()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
