import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Sparkles, FolderGit2, Plus, Settings, Play, CheckCircle2, ChevronDown } from 'lucide-react';

interface NavbarProps {
  onOpenNewProject: () => void;
  onOpenSettings: () => void;
  onRunAnalysis: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onOpenNewProject, onOpenSettings, onRunAnalysis }) => {
  const { projects, activeProject, setActiveProject, isAnalyzing } = useApp();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  return (
    <nav className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40 px-6 py-3">
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        {/* Brand Logo */}
        <div className="flex items-center space-x-6">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="h-5 w-5 text-white animate-pulse" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-100 to-slate-400 bg-clip-text text-transparent">
                ReqPilot<span className="text-indigo-400 font-extrabold ml-0.5">AI</span>
              </span>
              <span className="hidden sm:inline-block ml-2 text-[10px] font-semibold tracking-wider text-indigo-400 bg-indigo-950/80 border border-indigo-800/60 px-2 py-0.5 rounded-full uppercase">
                Multi-Agent v1.0
              </span>
            </div>
          </div>

          {/* Project Dropdown Selector */}
          <div className="relative">
            <button
              onClick={() => setDropdownOpen(!dropdownOpen)}
              className="flex items-center space-x-2 bg-slate-900 border border-slate-700/80 hover:border-slate-600 px-3.5 py-1.5 rounded-lg text-sm font-medium text-slate-200 transition-colors shadow-sm"
            >
              <FolderGit2 className="h-4 w-4 text-indigo-400" />
              <span className="max-w-[200px] truncate">{activeProject ? activeProject.title : 'Select Project'}</span>
              <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
            </button>

            {dropdownOpen && (
              <div className="absolute left-0 mt-2 w-72 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl z-50 p-1.5 animate-in fade-in slide-in-from-top-2">
                <div className="px-3 py-1.5 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                  Available Projects
                </div>
                <div className="max-h-60 overflow-y-auto space-y-1">
                  {projects.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => {
                        setActiveProject(p);
                        setDropdownOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between transition-colors ${
                        activeProject?.id === p.id
                          ? 'bg-indigo-600/20 text-indigo-300 font-medium'
                          : 'text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <span className="truncate">{p.title}</span>
                      {activeProject?.id === p.id && <CheckCircle2 className="h-4 w-4 text-indigo-400 ml-2 shrink-0" />}
                    </button>
                  ))}
                </div>
                <div className="border-t border-slate-800 mt-2 pt-2">
                  <button
                    onClick={() => {
                      setDropdownOpen(false);
                      onOpenNewProject();
                    }}
                    className="w-full text-left px-3 py-1.5 rounded-lg text-sm text-indigo-400 hover:bg-indigo-950/40 flex items-center space-x-2 transition-colors font-medium"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Create New Project</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-3">
          <button
            onClick={onRunAnalysis}
            disabled={isAnalyzing}
            className="flex items-center space-x-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white px-4 py-1.5 rounded-lg text-sm font-semibold shadow-md shadow-indigo-500/25 transition-all disabled:opacity-50"
          >
            {isAnalyzing ? (
              <>
                <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Running Agents...</span>
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-white" />
                <span>Analyze Requirements</span>
              </>
            )}
          </button>

          <button
            onClick={onOpenSettings}
            title="Settings & AI Model Provider"
            className="p-2 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 hover:text-white hover:border-slate-700 transition-colors"
          >
            <Settings className="h-4 w-4" />
          </button>

          {/* User Badge */}
          <div className="hidden md:flex items-center space-x-2 pl-2 border-l border-slate-800 text-xs">
            <div className="h-7 w-7 rounded-full bg-indigo-900 border border-indigo-700 flex items-center justify-center font-bold text-indigo-200">
              AM
            </div>
            <div className="text-left leading-tight">
              <p className="font-semibold text-slate-200">Alex Mercer</p>
              <p className="text-[10px] text-slate-400">Lead Analyst</p>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};
