import React from 'react';
import { useApp } from '../../context/AppContext';
import { Activity, ShieldCheck, AlertTriangle, Layers, Award } from 'lucide-react';

export const ProjectHeader: React.FC = () => {
  const { activeProject, stats } = useApp();

  if (!activeProject) return null;

  return (
    <div className="bg-slate-900/60 border-b border-slate-800/80 px-6 py-5">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        {/* Project Info */}
        <div className="space-y-1.5 max-w-3xl">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-white tracking-tight">{activeProject.title}</h1>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-blue-950/70 border border-blue-800/60 text-blue-400">
              {activeProject.domain}
            </span>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-950/70 border border-emerald-800/60 text-emerald-400 flex items-center space-x-1">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse mr-1" />
              Active
            </span>
          </div>
          <p className="text-sm text-slate-400 line-clamp-2 leading-relaxed">
            {activeProject.description}
          </p>
        </div>

        {/* Health Score & Live Stats Pill Grid */}
        <div className="flex items-center space-x-3 shrink-0">
          {/* Health Score Card */}
          <div className="glass-panel px-4 py-2.5 rounded-xl flex items-center space-x-3 border border-slate-700/60">
            <div className="h-10 w-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Health Score</div>
              <div className="text-xl font-bold text-emerald-400">
                {stats?.health_score ? `${stats.health_score}%` : '95%'}
              </div>
            </div>
          </div>

          {/* Requirements Stat */}
          <div className="glass-panel px-4 py-2.5 rounded-xl flex items-center space-x-3 border border-slate-700/60">
            <div className="h-10 w-10 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Requirements</div>
              <div className="text-base font-bold text-slate-200">
                {stats ? `${stats.approved_requirements} / ${stats.total_requirements}` : '0 / 0'}
              </div>
            </div>
          </div>

          {/* Issues Stat */}
          <div className="glass-panel px-4 py-2.5 rounded-xl flex items-center space-x-3 border border-slate-700/60">
            <div className="h-10 w-10 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Issues</div>
              <div className="text-base font-bold text-amber-400">
                {stats ? `${stats.open_issues} Open` : '0 Open'}
              </div>
            </div>
          </div>

          {/* Quality Stat */}
          <div className="glass-panel px-4 py-2.5 rounded-xl flex items-center space-x-3 border border-slate-700/60">
            <div className="h-10 w-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Award className="h-5 w-5" />
            </div>
            <div>
              <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">Avg Quality</div>
              <div className="text-base font-bold text-purple-400">
                {stats?.average_quality_score ? `${stats.average_quality_score}%` : '88%'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
