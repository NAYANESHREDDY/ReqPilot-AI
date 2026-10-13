import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { ArchitectureModule, ArchitectureRelation } from '../../types';
import {
  Network, Server, Database, Shield, Globe, Layers, Plus,
  Sparkles, ExternalLink, Code2, ArrowRight
} from 'lucide-react';

export const ArchitectureTab: React.FC = () => {
  const { activeProject, showToast } = useApp();
  const [modules, setModules] = useState<ArchitectureModule[]>([]);
  const [relations, setRelations] = useState<ArchitectureRelation[]>([]);
  const [selectedModule, setSelectedModule] = useState<ArchitectureModule | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Add Module Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newModName, setNewModName] = useState('');
  const [newModDesc, setNewModDesc] = useState('');
  const [newModType, setNewModType] = useState<'service' | 'database' | 'gateway'>('service');
  const [newModStack, setNewModStack] = useState('');

  const loadArchitecture = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getArchitecture(activeProject.id);
      setModules(data.modules);
      setRelations(data.relations);
      if (data.modules.length > 0 && !selectedModule) {
        setSelectedModule(data.modules[0]);
      }
    } catch (e) {
      console.error('Error loading architecture', e);
    }
  };

  useEffect(() => {
    loadArchitecture();
  }, [activeProject]);

  const handleRegenerate = async () => {
    if (!activeProject) return;
    setIsRegenerating(true);
    try {
      const data = await api.generateArchitecture(activeProject.id);
      setModules(data.modules);
      setRelations(data.relations);
      showToast('Candidate architecture synthesized from requirements!', 'success');
      if (data.modules.length > 0) setSelectedModule(data.modules[0]);
    } catch (e) {
      showToast('Failed to regenerate architecture', 'error');
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleAddModule = async () => {
    if (!newModName.trim() || !activeProject) return;
    try {
      const created = await api.createRequirement(activeProject.id, {}); // or module endpoint
      // Call create module API directly
      const res = await fetch(`/api/projects/${activeProject.id}/architecture/modules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newModName,
          description: newModDesc,
          module_type: newModType,
          tech_stack: newModStack || 'FastAPI / Python',
          responsibilities: ['Core microservice functionality'],
          api_endpoints: [`/api/${newModName.toLowerCase().replace(/\s+/g, '-')}`],
        }),
      });
      if (!res.ok) throw new Error('Create module failed');
      showToast(`Module "${newModName}" created!`, 'success');
      setShowAddModal(false);
      setNewModName('');
      setNewModDesc('');
      await loadArchitecture();
    } catch (e) {
      showToast('Failed to add module', 'error');
    }
  };

  const getModuleIcon = (type: string) => {
    switch (type) {
      case 'database':
        return <Database className="h-5 w-5 text-purple-400" />;
      case 'gateway':
        return <Globe className="h-5 w-5 text-blue-400" />;
      default:
        return <Server className="h-5 w-5 text-emerald-400" />;
    }
  };

  const getModuleBorder = (type: string, isSelected: boolean) => {
    if (isSelected) return 'border-indigo-500 ring-2 ring-indigo-500/30 bg-indigo-950/40 shadow-xl';
    switch (type) {
      case 'database':
        return 'border-purple-800/60 hover:border-purple-600 bg-purple-950/20';
      case 'gateway':
        return 'border-blue-800/60 hover:border-blue-600 bg-blue-950/20';
      default:
        return 'border-emerald-800/60 hover:border-emerald-600 bg-emerald-950/20';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Network className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white">System Architecture & Service Boundaries (Section 12)</h3>
            <p className="text-xs text-slate-400">
              Candidate modules, inter-service calls, pub/sub queues, and database relationships synthesized from approved requirements.
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAddModal(true)}
            className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add Module</span>
          </button>
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating}
            className="bg-indigo-600 hover:bg-indigo-500 text-white px-3.5 py-1.5 rounded-xl text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>{isRegenerating ? 'Generating...' : 'Regenerate Architecture'}</span>
          </button>
        </div>
      </div>

      {/* Main Split View: Visual Graph & Inspector Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Visual Graph Topology */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-3">
            <span>Click any node to inspect service contract and endpoints</span>
            <div className="flex items-center space-x-3">
              <span className="flex items-center space-x-1">
                <span className="h-2 w-2 rounded-full bg-blue-400" />
                <span>Gateway</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                <span>Microservice</span>
              </span>
              <span className="flex items-center space-x-1">
                <span className="h-2 w-2 rounded-full bg-purple-400" />
                <span>Database</span>
              </span>
            </div>
          </div>

          {/* Topology Node Canvas */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-2">
            {modules.map((m) => {
              const isSelected = selectedModule?.id === m.id;

              return (
                <div
                  key={m.id}
                  onClick={() => setSelectedModule(m)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2 ${getModuleBorder(
                    m.module_type,
                    isSelected
                  )}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      {getModuleIcon(m.module_type)}
                      <span className="font-mono text-xs font-bold text-white">{m.id}</span>
                    </div>
                    <span className="text-[10px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                      {m.module_type}
                    </span>
                  </div>

                  <h4 className="text-xs font-bold text-white leading-snug">{m.name}</h4>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{m.description}</p>

                  <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-500">
                    <span className="truncate max-w-[120px]">{m.tech_stack}</span>
                    <span className="text-indigo-400 font-semibold">{m.api_endpoints?.length || 0} APIs</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Directed Relationships Table */}
          <div className="pt-4 border-t border-slate-800 space-y-2">
            <h5 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
              Inter-Module Directed Relations ({relations.length})
            </h5>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
              {relations.map((rel) => (
                <div
                  key={rel.id}
                  className="bg-slate-900/80 border border-slate-800/80 p-2 rounded-lg flex items-center justify-between"
                >
                  <div className="flex items-center space-x-1.5 font-mono text-[11px]">
                    <span className="text-indigo-300">{rel.source_module_id}</span>
                    <span className="text-slate-500">--[{rel.relation_type}]--&gt;</span>
                    <span className="text-emerald-300">{rel.target_module_id}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 truncate max-w-[120px]">{rel.description}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Selected Module Inspector Drawer */}
        <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Code2 className="h-5 w-5 text-indigo-400" />
              <h4 className="text-sm font-bold text-white">Module Contract Inspector</h4>
            </div>
            {selectedModule && (
              <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950/80 border border-indigo-700/60 px-2 py-0.5 rounded">
                {selectedModule.id}
              </span>
            )}
          </div>

          {!selectedModule ? (
            <div className="text-center py-12 text-xs text-slate-500">
              Select any architecture module on the left to inspect its contract.
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">Service Name</span>
                <p className="text-sm font-bold text-white">{selectedModule.name}</p>
                <p className="text-slate-300 mt-1 leading-relaxed">{selectedModule.description}</p>
              </div>

              <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
                  Technology Stack
                </span>
                <span className="font-mono text-xs text-indigo-300 font-semibold">{selectedModule.tech_stack}</span>
              </div>

              {selectedModule.responsibilities && selectedModule.responsibilities.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                    Core Responsibilities
                  </span>
                  <ul className="space-y-1">
                    {selectedModule.responsibilities.map((resp, i) => (
                      <li key={i} className="flex items-center space-x-2 text-slate-300">
                        <ArrowRight className="h-3 w-3 text-indigo-400 shrink-0" />
                        <span>{resp}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedModule.api_endpoints && selectedModule.api_endpoints.length > 0 && (
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 block">
                    Exposed API Contracts
                  </span>
                  <div className="space-y-1">
                    {selectedModule.api_endpoints.map((ep, i) => (
                      <div
                        key={i}
                        className="font-mono text-[11px] bg-slate-950 p-2 rounded-lg border border-slate-800 text-emerald-400"
                      >
                        {ep}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Add Module Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-base font-bold text-white">Add Architecture Module</h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Module Name</label>
                <input
                  type="text"
                  placeholder="e.g. Analytics & Telemetry Service"
                  value={newModName}
                  onChange={(e) => setNewModName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Description</label>
                <textarea
                  rows={2}
                  placeholder="Describe module role..."
                  value={newModDesc}
                  onChange={(e) => setNewModDesc(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Module Type</label>
                <select
                  value={newModType}
                  onChange={(e) => setNewModType(e.target.value as any)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="service">Microservice</option>
                  <option value="gateway">API Gateway / Edge</option>
                  <option value="database">Database / Data Lake</option>
                </select>
              </div>

              <div>
                <label className="block text-slate-400 mb-1 font-semibold">Tech Stack</label>
                <input
                  type="text"
                  placeholder="e.g. Python FastAPI / ClickHouse"
                  value={newModStack}
                  onChange={(e) => setNewModStack(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-2.5 text-white focus:outline-none focus:border-indigo-500"
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
                onClick={handleAddModule}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/30"
              >
                Create Module
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
