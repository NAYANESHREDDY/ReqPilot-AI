import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { TraceabilityResponse } from '../../types';
import { GitMerge, CheckCircle2, AlertTriangle, Search, FileText, ArrowRight } from 'lucide-react';

export const TraceabilityTab: React.FC = () => {
  const { activeProject } = useApp();
  const [data, setData] = useState<TraceabilityResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showOrphansOnly, setShowOrphansOnly] = useState(false);

  const loadTraceability = async () => {
    if (!activeProject) return;
    try {
      const res = await api.getTraceability(activeProject.id);
      setData(res);
    } catch (e) {
      console.error('Failed to load traceability', e);
    }
  };

  useEffect(() => {
    loadTraceability();
  }, [activeProject]);

  if (!data) return null;

  const filteredMatrix = data.matrix.filter((row) => {
    if (showOrphansOnly && !row.is_orphan) return false;
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      row.requirement_id.toLowerCase().includes(q) ||
      row.requirement_summary.toLowerCase().includes(q) ||
      (row.module_name && row.module_name.toLowerCase().includes(q))
    );
  });

  return (
    <div className="space-y-6">
      {/* Header & Metrics Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <CheckCircle2 className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Test & Task Coverage</div>
            <div className="text-xl font-bold text-emerald-400">{data.coverage_pct}%</div>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <GitMerge className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Fully Linked</div>
            <div className="text-xl font-bold text-white">{data.fully_linked_count} Reqs</div>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
            <AlertTriangle className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Orphan Requirements</div>
            <div className="text-xl font-bold text-amber-400">{data.orphan_count} Unlinked</div>
          </div>
        </div>

        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex items-center space-x-3">
          <div className="h-10 w-10 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <FileText className="h-5 w-5" />
          </div>
          <div>
            <div className="text-[10px] text-slate-400 uppercase font-semibold">Total Audited</div>
            <div className="text-xl font-bold text-white">{data.total_requirements} Reqs</div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3.5 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search matrix by ID, summary, module..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowOrphansOnly(!showOrphansOnly)}
            className={`px-3 py-1.5 rounded-xl text-xs font-semibold border transition-all ${
              showOrphansOnly
                ? 'bg-amber-600/30 border-amber-500 text-amber-300'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            {showOrphansOnly ? 'Showing Orphans Only' : 'Filter Orphans'}
          </button>
        </div>
      </div>

      {/* Traceability Matrix Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 border-b border-slate-800 text-[11px] uppercase font-bold text-slate-400 tracking-wider">
              <tr>
                <th className="p-3.5">Source Evidence</th>
                <th className="p-3.5">Requirement</th>
                <th className="p-3.5">Architecture Module</th>
                <th className="p-3.5">Development Tasks</th>
                <th className="p-3.5">Test Verification</th>
                <th className="p-3.5 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80">
              {filteredMatrix.map((row) => (
                <tr key={row.requirement_id} className="hover:bg-slate-900/50 transition-colors">
                  {/* Source */}
                  <td className="p-3.5 whitespace-nowrap">
                    <div className="flex items-center space-x-1.5 font-medium text-slate-300">
                      <FileText className="h-3.5 w-3.5 text-slate-500" />
                      <span className="truncate max-w-[120px]">{row.source_id}</span>
                      <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                        p{row.source_page}
                      </span>
                    </div>
                  </td>

                  {/* Requirement */}
                  <td className="p-3.5">
                    <div className="space-y-0.5 max-w-sm">
                      <div className="flex items-center space-x-1.5">
                        <span className="font-mono text-[11px] font-bold text-indigo-400">{row.requirement_id}</span>
                        <span className="text-[9px] uppercase font-bold px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                          {row.req_type}
                        </span>
                      </div>
                      <p className="text-slate-200 line-clamp-1 font-medium">{row.requirement_summary}</p>
                    </div>
                  </td>

                  {/* Module */}
                  <td className="p-3.5 whitespace-nowrap">
                    <span className="font-mono text-[11px] font-semibold text-emerald-400 bg-emerald-950/40 border border-emerald-900/40 px-2 py-0.5 rounded">
                      {row.module_id || 'MOD-CORE'}
                    </span>
                  </td>

                  {/* Tasks */}
                  <td className="p-3.5">
                    {row.task_ids && row.task_ids.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {row.task_ids.map((tid) => (
                          <span
                            key={tid}
                            className="font-mono text-[10px] bg-slate-800 text-slate-300 border border-slate-700 px-1.5 py-0.5 rounded"
                          >
                            {tid}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[11px] text-amber-400 italic">No task assigned</span>
                    )}
                  </td>

                  {/* Tests */}
                  <td className="p-3.5">
                    {row.test_ids && row.test_ids.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {row.test_ids.map((tcid) => (
                          <span
                            key={tcid}
                            className="font-mono text-[10px] bg-purple-950/60 text-purple-300 border border-purple-800/60 px-1.5 py-0.5 rounded"
                          >
                            {tcid}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[11px] text-amber-400 italic">No test created</span>
                    )}
                  </td>

                  {/* Status Badge */}
                  <td className="p-3.5 text-center whitespace-nowrap">
                    {row.is_orphan ? (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-950/80 border border-amber-800/80 text-amber-300">
                        Orphan
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-800/80 text-emerald-300 flex items-center justify-center space-x-1">
                        <CheckCircle2 className="h-3 w-3 mr-1" />
                        Linked
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
