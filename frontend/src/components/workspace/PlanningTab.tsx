import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { Task, TeamMember } from '../../types';
import {
  Kanban as KanbanIcon, ListTodo, Calendar, Clock, User, CheckCircle2,
  ChevronRight, ArrowRight, Sparkles, Filter, AlertCircle
} from 'lucide-react';

export const PlanningTab: React.FC = () => {
  const { activeProject, refreshStats, showToast } = useApp();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [viewMode, setViewMode] = useState<'kanban' | 'sprints'>('kanban');
  const [selectedSprint, setSelectedSprint] = useState<string>('all');

  const loadPlanningData = async () => {
    if (!activeProject) return;
    try {
      const [taskData, teamData] = await Promise.all([
        api.getTasks(activeProject.id),
        api.getTeam(activeProject.id),
      ]);
      setTasks(taskData);
      setTeam(teamData);
    } catch (e) {
      console.error('Failed to load planning data', e);
    }
  };

  useEffect(() => {
    loadPlanningData();
  }, [activeProject]);

  const handleStatusChange = async (task: Task, newStatus: string) => {
    try {
      await api.updateTaskStatus(task.id, newStatus);
      showToast(`Task ${task.id} moved to ${newStatus.replace('_', ' ').toUpperCase()}!`, 'success');
      await loadPlanningData();
      await refreshStats();
    } catch (e) {
      showToast('Failed to update task status', 'error');
    }
  };

  const kanbanColumns = [
    { id: 'todo', title: 'To Do', color: 'border-slate-700 bg-slate-900/40 text-slate-300' },
    { id: 'in_progress', title: 'In Progress', color: 'border-blue-700/60 bg-blue-950/20 text-blue-300' },
    { id: 'review', title: 'Review & QA', color: 'border-purple-700/60 bg-purple-950/20 text-purple-300' },
    { id: 'done', title: 'Done', color: 'border-emerald-700/60 bg-emerald-950/20 text-emerald-300' },
  ];

  const filteredTasks = tasks.filter((t) => {
    if (selectedSprint === 'all') return true;
    return t.sprint_name === selectedSprint;
  });

  const uniqueSprints = Array.from(new Set(tasks.map((t) => t.sprint_name).filter(Boolean)));

  return (
    <div className="space-y-6">
      {/* Controls Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <KanbanIcon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Project Planning & Sprint Board (Section 13 & 28)</h3>
            <p className="text-xs text-slate-400">
              Tasks decomposed from requirements with cycle-free DAG dependencies, complexity estimates, and sprint allocation.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* View Toggle */}
          <div className="inline-flex rounded-xl bg-slate-900 border border-slate-800 p-1">
            <button
              onClick={() => setViewMode('kanban')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                viewMode === 'kanban' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <KanbanIcon className="h-3.5 w-3.5" />
              <span>Kanban Board</span>
            </button>
            <button
              onClick={() => setViewMode('sprints')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all ${
                viewMode === 'sprints' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              <Calendar className="h-3.5 w-3.5" />
              <span>Sprint Roadmap</span>
            </button>
          </div>

          {/* Sprint Filter */}
          {uniqueSprints.length > 0 && (
            <select
              value={selectedSprint}
              onChange={(e) => setSelectedSprint(e.target.value)}
              className="bg-slate-900 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="all">All Sprints</option>
              {uniqueSprints.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Kanban Board View */}
      {viewMode === 'kanban' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {kanbanColumns.map((col) => {
            const colTasks = filteredTasks.filter((t) => t.status === col.id);

            return (
              <div
                key={col.id}
                className="bg-slate-950/60 rounded-2xl border border-slate-800/80 p-4 space-y-3 flex flex-col min-h-[600px]"
              >
                {/* Column Header */}
                <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                  <span className={`text-xs font-bold uppercase tracking-wider ${col.color.split(' ')[2]}`}>
                    {col.title}
                  </span>
                  <span className="text-xs font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full border border-slate-800">
                    {colTasks.length}
                  </span>
                </div>

                {/* Task Cards Column */}
                <div className="space-y-3 flex-1 overflow-y-auto pr-1">
                  {colTasks.map((t) => (
                    <div
                      key={t.id}
                      className="bg-slate-900/90 border border-slate-800 hover:border-slate-700 p-4 rounded-xl space-y-3 shadow-md transition-all group"
                    >
                      {/* Top Badges */}
                      <div className="flex items-center justify-between text-[10px]">
                        <div className="flex items-center space-x-1.5 font-mono font-bold text-white">
                          <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-700">{t.id}</span>
                          {t.requirement_id && (
                            <span className="bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-800">
                              {t.requirement_id}
                            </span>
                          )}
                        </div>

                        <span
                          className={`uppercase font-bold tracking-wider px-1.5 py-0.5 rounded border ${
                            t.complexity === 'high'
                              ? 'bg-red-950/70 text-red-300 border-red-800/60'
                              : 'bg-blue-950/70 text-blue-300 border-blue-800/60'
                          }`}
                        >
                          {t.complexity}
                        </span>
                      </div>

                      {/* Title */}
                      <h4 className="text-xs font-bold text-white leading-snug">{t.title}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2">{t.description}</p>

                      {/* Points & Assignee Row */}
                      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-indigo-300">{t.story_points} pts</span>
                          <span>•</span>
                          <span>{t.estimated_hours}h</span>
                        </div>

                        <span className="flex items-center text-slate-300 font-medium">
                          <User className="h-3 w-3 mr-1 text-slate-400" />
                          <span className="truncate max-w-[100px]">{t.assignee_name}</span>
                        </span>
                      </div>

                      {/* Status Transition Quick Buttons */}
                      <div className="pt-2 flex items-center justify-end space-x-1 border-t border-slate-800/50">
                        {col.id !== 'todo' && (
                          <button
                            onClick={() => handleStatusChange(t, col.id === 'done' ? 'review' : (col.id === 'review' ? 'in_progress' : 'todo'))}
                            className="text-[10px] text-slate-400 hover:text-white px-2 py-0.5 rounded bg-slate-800"
                          >
                            ← Back
                          </button>
                        )}
                        {col.id !== 'done' && (
                          <button
                            onClick={() => handleStatusChange(t, col.id === 'todo' ? 'in_progress' : (col.id === 'in_progress' ? 'review' : 'done'))}
                            className="text-[10px] text-indigo-300 hover:text-white px-2 py-0.5 rounded bg-indigo-950 border border-indigo-800"
                          >
                            Advance →
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Sprints Roadmap View */}
      {viewMode === 'sprints' && (
        <div className="space-y-4">
          {uniqueSprints.map((sprintName) => {
            const sprintTasks = tasks.filter((t) => t.sprint_name === sprintName);
            const totalPoints = sprintTasks.reduce((acc, t) => acc + (t.story_points || 0), 0);
            const donePoints = sprintTasks.filter((t) => t.status === 'done').reduce((acc, t) => acc + (t.story_points || 0), 0);

            return (
              <div key={sprintName} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Calendar className="h-5 w-5 text-indigo-400" />
                    <div>
                      <h4 className="text-sm font-bold text-white">{sprintName}</h4>
                      <p className="text-xs text-slate-400">{sprintTasks.length} tasks allocated • {totalPoints} story points</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 text-xs">
                    <span className="text-slate-400">Progress:</span>
                    <span className="font-bold text-emerald-400">
                      {totalPoints > 0 ? Math.round((donePoints / totalPoints) * 100) : 0}%
                    </span>
                  </div>
                </div>

                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2 rounded-full"
                    style={{ width: `${totalPoints > 0 ? (donePoints / totalPoints) * 100 : 0}%` }}
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2.5 pt-2">
                  {sprintTasks.map((t) => (
                    <div
                      key={t.id}
                      className="bg-slate-900/80 border border-slate-800/80 p-3 rounded-xl flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5 truncate pr-2">
                        <span className="font-mono text-[10px] text-indigo-300 font-bold block">{t.id}</span>
                        <span className="font-semibold text-slate-200 truncate block">{t.title}</span>
                      </div>
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border shrink-0 ${
                          t.status === 'done' ? 'bg-emerald-950 text-emerald-400 border-emerald-800' : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
