import React from 'react';
import { useApp } from '../../context/AppContext';
import {
  LayoutDashboard, FileText, CheckSquare, AlertCircle, HelpCircle,
  Network, Kanban, Users, GitMerge, Zap, BookOpen, BarChart3
} from 'lucide-react';

export const TabNavigation: React.FC = () => {
  const { activeTab, setActiveTab, stats } = useApp();

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'sources', label: 'Sources', icon: FileText },
    {
      id: 'requirements',
      label: 'Requirements',
      icon: CheckSquare,
      badge: stats?.total_requirements || null,
    },
    {
      id: 'issues',
      label: 'AI Issues',
      icon: AlertCircle,
      badge: stats?.open_issues || null,
      badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/30',
    },
    { id: 'clarifications', label: 'Clarifications', icon: HelpCircle },
    { id: 'architecture', label: 'Architecture', icon: Network },
    {
      id: 'planning',
      label: 'Planning',
      icon: Kanban,
      badge: stats?.total_tasks || null,
    },
    { id: 'team', label: 'Team & Skills', icon: Users },
    { id: 'traceability', label: 'Traceability', icon: GitMerge },
    {
      id: 'change_impact',
      label: 'Change Impact',
      icon: Zap,
      highlight: true,
    },
    { id: 'reports', label: 'Reports', icon: BookOpen },
    { id: 'evaluation', label: 'Benchmarks', icon: BarChart3 },
  ];

  return (
    <div className="border-b border-slate-800 bg-slate-950 px-6 overflow-x-auto scrollbar-none">
      <div className="max-w-7xl mx-auto flex items-center space-x-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 px-3.5 py-3 text-xs font-semibold whitespace-nowrap transition-all border-b-2 ${
                isActive
                  ? 'border-indigo-500 text-indigo-400 bg-indigo-950/20'
                  : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
              } ${tab.highlight && !isActive ? 'text-amber-400/90' : ''}`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-indigo-400' : 'text-slate-400'}`} />
              <span>{tab.label}</span>

              {tab.badge !== null && tab.badge !== undefined && (
                <span
                  className={`ml-1.5 px-1.5 py-0.5 rounded-full text-[10px] font-bold border ${
                    tab.badgeColor || 'bg-slate-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {tab.badge}
                </span>
              )}

              {tab.highlight && (
                <span className="ml-1 text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.2 rounded bg-gradient-to-r from-amber-500/20 to-orange-500/20 text-amber-300 border border-amber-500/30">
                  Feature
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
};
