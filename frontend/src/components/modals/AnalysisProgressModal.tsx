import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import {
  Sparkles, CheckCircle2, Clock, AlertTriangle, Terminal, X,
  ArrowRight, ShieldCheck, Layers, FileText
} from 'lucide-react';

interface AnalysisProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AnalysisProgressModal: React.FC<AnalysisProgressModalProps> = ({ isOpen, onClose }) => {
  const { activeProject, refreshStats, refreshProjects, setActiveTab, apiKey, provider, showToast } = useApp();
  const [isRunning, setIsRunning] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [summaryResult, setSummaryResult] = useState<any | null>(null);

  const steps = [
    { title: '1. Ingestion & Document Chunking', agent: 'Document Ingestion Agent' },
    { title: '2. Structured Requirement Extraction', agent: 'Extraction Agent (Evidence Grounding)' },
    { title: '3. 7-Dimension Quality Scoring', agent: 'Quality Evaluation Agent' },
    { title: '4. Ambiguity, Conflict & Duplicate Audit', agent: '3-Stage Conflict & Ambiguity Engine' },
    { title: '5. Candidate Architecture Synthesis', agent: 'Architecture Agent' },
    { title: '6. Task Hierarchy & DAG Sprints', agent: 'Task Decomposition & Scheduling Agent' },
    { title: '7. Traceability Matrix & 6 Reports', agent: 'Traceability & Report Generation Agent' },
  ];

  const startAnalysis = async () => {
    if (!activeProject) return;
    setIsRunning(true);
    setSummaryResult(null);
    setLogs(['Initiating ReqPilot AI Multi-Agent Pipeline...']);
    setCurrentStep(1);

    try {
      // Step simulated progression for crisp feedback
      const timer1 = setTimeout(() => {
        setCurrentStep(2);
        setLogs((prev) => [...prev, 'Running Extraction Agent: identifying functional & non-functional requirements with citations...']);
      }, 700);

      const timer2 = setTimeout(() => {
        setCurrentStep(3);
        setLogs((prev) => [...prev, 'Running Quality Agent: computing completeness, clarity, testability, atomicity...']);
      }, 1500);

      const timer3 = setTimeout(() => {
        setCurrentStep(4);
        setLogs((prev) => [...prev, 'Running Conflict & Ambiguity Agent: checking 3-stage candidate pairs and subjective terms...']);
      }, 2300);

      const timer4 = setTimeout(() => {
        setCurrentStep(5);
        setLogs((prev) => [...prev, 'Running Architecture Agent: generating microservices, data domains, and gateway routes...']);
      }, 3100);

      const timer5 = setTimeout(() => {
        setCurrentStep(6);
        setLogs((prev) => [...prev, 'Running Task Agent: building Epics -> Features -> Tasks -> DAG Sprints...']);
      }, 3900);

      const timer6 = setTimeout(() => {
        setCurrentStep(7);
        setLogs((prev) => [...prev, 'Compiling Traceability Matrix and generating all 6 formal engineering reports...']);
      }, 4700);

      const useLlm = provider !== 'offline';

      const res = await api.triggerAnalysis(
        activeProject.id,
        useLlm,
        apiKey || undefined,
        provider
      );

      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
      clearTimeout(timer4);
      clearTimeout(timer5);
      clearTimeout(timer6);

      setCurrentStep(7);
      setSummaryResult(res);
      setLogs(res.logs || []);
      showToast('Multi-Agent Analysis successfully completed!', 'success');
      await refreshStats();
      await refreshProjects();
    } catch (err) {
      showToast('Analysis encountered an error', 'error');
      setLogs((prev) => [...prev, 'Error during agent execution. Please check document sources.']);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      startAnalysis();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-500 flex items-center justify-center text-white shadow-md">
              <Sparkles className="h-5 w-5 animate-pulse" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Multi-Agent Workflow Orchestrator</h3>
              <p className="text-xs text-slate-400">Section 8: 15 Specialized Autonomous Engineering Agents</p>
            </div>
          </div>
          {!isRunning && (
            <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {/* Stepper Grid */}
        <div className="space-y-2 shrink-0">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            {steps.map((st, i) => {
              const stepNum = i + 1;
              const isDone = currentStep > stepNum || summaryResult;
              const isCurrent = currentStep === stepNum && isRunning;

              return (
                <div
                  key={i}
                  className={`p-2.5 rounded-xl border flex items-center justify-between transition-all ${
                    isDone
                      ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300'
                      : isCurrent
                      ? 'bg-indigo-950/50 border-indigo-500 text-white shadow-md animate-pulse'
                      : 'bg-slate-950/40 border-slate-800/80 text-slate-500'
                  }`}
                >
                  <div className="truncate mr-2">
                    <span className="font-semibold block truncate">{st.title}</span>
                    <span className="text-[10px] text-slate-400 block truncate">{st.agent}</span>
                  </div>

                  {isDone ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
                  ) : isCurrent ? (
                    <div className="h-4 w-4 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin shrink-0" />
                  ) : (
                    <div className="h-2 w-2 rounded-full bg-slate-700 shrink-0" />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Terminal Log Console */}
        <div className="flex-1 bg-slate-950 border border-slate-800 rounded-xl p-3 font-mono text-[11px] text-slate-300 overflow-y-auto space-y-1 min-h-[140px] max-h-[220px]">
          <div className="flex items-center space-x-2 text-slate-500 text-[10px] border-b border-slate-800/80 pb-1.5 mb-1.5">
            <Terminal className="h-3 w-3" />
            <span>Agent Execution Live Terminal Log</span>
          </div>
          {logs.map((msg, idx) => (
            <div key={idx} className="flex items-start space-x-2">
              <span className="text-indigo-400 select-none">&gt;</span>
              <span className="leading-relaxed">{msg}</span>
            </div>
          ))}
        </div>

        {/* Summary Results when Finished */}
        {summaryResult && (
          <div className="bg-gradient-to-r from-indigo-950/60 via-slate-900 to-emerald-950/60 p-4 rounded-xl border border-indigo-800/50 flex items-center justify-between shrink-0 animate-in fade-in">
            <div className="grid grid-cols-4 gap-4 text-center">
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Requirements</span>
                <span className="text-base font-bold text-white">{summaryResult.extracted_requirements}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Issues</span>
                <span className="text-base font-bold text-amber-400">{summaryResult.detected_issues}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Modules</span>
                <span className="text-base font-bold text-emerald-400">{summaryResult.generated_modules}</span>
              </div>
              <div>
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Tasks</span>
                <span className="text-base font-bold text-purple-400">{summaryResult.generated_tasks}</span>
              </div>
            </div>

            <button
              onClick={() => {
                onClose();
                setActiveTab('requirements');
              }}
              className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-bold flex items-center space-x-1.5 shadow-md shadow-indigo-600/30 transition-all shrink-0 ml-4"
            >
              <span>View Requirements</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
