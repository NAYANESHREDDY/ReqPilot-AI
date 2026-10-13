import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { TeamMember } from '../../types';
import { Users, UserCheck, Plus, Sparkles, Activity, Shield, Award } from 'lucide-react';

export const TeamTab: React.FC = () => {
  const { activeProject, showToast } = useApp();
  const [team, setTeam] = useState<TeamMember[]>([]);
  const [assignmentLogs, setAssignmentLogs] = useState<any[]>([]);
  const [isAssigning, setIsAssigning] = useState(false);

  // Add Member Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [name, setName] = useState('');
  const [role, setRole] = useState('Senior Full Stack Developer');
  const [email, setEmail] = useState('');
  const [primarySkill, setPrimarySkill] = useState('Python');
  const [primaryProficiency, setPrimaryProficiency] = useState(90);

  const loadTeam = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getTeam(activeProject.id);
      setTeam(data);
    } catch (e) {
      console.error('Error loading team', e);
    }
  };

  useEffect(() => {
    loadTeam();
  }, [activeProject]);

  const handleAutoAssign = async () => {
    if (!activeProject) return;
    setIsAssigning(true);
    try {
      const res = await api.autoAssignTeam(activeProject.id);
      setAssignmentLogs(res.assignments || []);
      showToast('AI successfully allocated tasks based on skill proficiency and availability!', 'success');
      await loadTeam();
    } catch (e) {
      showToast('Auto-assignment failed', 'error');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleAddMember = async () => {
    if (!name.trim() || !activeProject) return;
    try {
      const skills: Record<string, number> = {};
      const seen = new Set<string>();
      for (const raw of primarySkill.split(',')) {
        const skillName = raw.trim();
        if (!skillName) continue;
        const dedupeKey = skillName.toLowerCase();
        if (seen.has(dedupeKey)) continue;
        seen.add(dedupeKey);
        skills[skillName] = primaryProficiency;
      }

      const res = await fetch(`/api/projects/${activeProject.id}/team`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name,
          email,
          role,
          capacity_hours_per_week: 40.0,
          skills,
        }),
      });
      if (!res.ok) throw new Error('Create member failed');
      showToast(`Team member "${name}" added!`, 'success');
      setShowAddModal(false);
      setName('');
      setEmail('');
      await loadTeam();
    } catch (e) {
      showToast('Failed to add team member', 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Users className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">Team Roster & Skill Matching Engine (Section 29)</h3>
            <p className="text-xs text-slate-400">
              Matches tasks to developers using: Score = (0.50 × SkillMatch) + (0.25 × Availability) + (0.25 × Workload).
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Member</span>
          </button>
          <button
            onClick={handleAutoAssign}
            disabled={isAssigning}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>{isAssigning ? 'Matching...' : 'Auto-Assign Tasks with AI'}</span>
          </button>
        </div>
      </div>

      {/* Team Member Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {team.map((member) => (
          <div
            key={member.id}
            className="glass-panel p-5 rounded-2xl border border-slate-800 hover:border-slate-700 transition-all space-y-4"
          >
            {/* User Info */}
            <div className="flex items-center space-x-3">
              <div className="h-11 w-11 rounded-xl bg-gradient-to-tr from-indigo-900 to-purple-900 border border-indigo-700 flex items-center justify-center text-sm font-bold text-indigo-200">
                {member.name.split(' ').map((n) => n[0]).join('')}
              </div>
              <div className="truncate">
                <h4 className="text-sm font-bold text-white truncate">{member.name}</h4>
                <p className="text-[11px] text-indigo-400 font-medium truncate">{member.role}</p>
              </div>
            </div>

            {/* Current Workload Meter */}
            <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-400">Current Workload:</span>
                <span className="font-bold text-white">{member.current_load_pct}%</span>
              </div>
              <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div
                  className={`h-1.5 rounded-full ${
                    member.current_load_pct > 80 ? 'bg-red-500' : 'bg-emerald-500'
                  }`}
                  style={{ width: `${member.current_load_pct}%` }}
                />
              </div>
            </div>

            {/* Skills Bars */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                Skill Proficiencies
              </span>
              <div className="space-y-1.5">
                {Object.entries(member.skills || {}).slice(0, 4).map(([skill, prof]) => (
                  <div key={skill} className="space-y-0.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-slate-300 font-medium">{skill}</span>
                      <span className="text-indigo-400 font-bold">{prof}%</span>
                    </div>
                    <div className="w-full bg-slate-800 h-1 rounded-full overflow-hidden">
                      <div className="bg-indigo-500 h-1 rounded-full" style={{ width: `${prof}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* AI Assignment Decisions Console */}
      {assignmentLogs.length > 0 && (
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
          <h4 className="text-sm font-bold text-white flex items-center space-x-2">
            <UserCheck className="h-4 w-4 text-emerald-400" />
            <span>AI Skill Matching Allocation Audit</span>
          </h4>

          <div className="space-y-2 max-h-60 overflow-y-auto pr-1 text-xs">
            {assignmentLogs.map((log, i) => (
              <div
                key={i}
                className="bg-slate-900/80 border border-slate-800/80 p-3 rounded-xl flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-indigo-300">{log.task_id}</span>
                    <span className="font-semibold text-white">{log.task_title}</span>
                  </div>
                  <p className="text-[11px] text-slate-400">{log.reasoning}</p>
                </div>
                <div className="text-right shrink-0 ml-4">
                  <span className="text-xs font-bold text-emerald-400 block">{log.match_pct}% Match</span>
                  <span className="text-[10px] text-slate-300 font-semibold">{log.assignee}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Member Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Add Team Member</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Full Name</label>
                <input
                  type="text"
                  placeholder="e.g. Elena Rostova"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Role</label>
                <input
                  type="text"
                  placeholder="e.g. Senior Backend Engineer"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Skills</label>
                <input
                  type="text"
                  placeholder="e.g. FastAPI, Authentication, SQL"
                  value={primarySkill}
                  onChange={(e) => setPrimarySkill(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Skill Proficiency: {primaryProficiency}%</label>
                <input
                  type="range"
                  min="40"
                  max="100"
                  value={primaryProficiency}
                  onChange={(e) => setPrimaryProficiency(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
              <button
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleAddMember}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
              >
                Save Member
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
