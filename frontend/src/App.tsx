import React, { useState } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { Navbar } from './components/layout/Navbar';
import { ProjectHeader } from './components/layout/ProjectHeader';
import { TabNavigation } from './components/layout/TabNavigation';

// Workspace Tabs
import { OverviewTab } from './components/workspace/OverviewTab';
import { SourcesTab } from './components/workspace/SourcesTab';
import { RequirementsTab } from './components/workspace/RequirementsTab';
import { IssuesTab } from './components/workspace/IssuesTab';
import { ClarificationsTab } from './components/workspace/ClarificationsTab';
import { ArchitectureTab } from './components/workspace/ArchitectureTab';
import { PlanningTab } from './components/workspace/PlanningTab';
import { TeamTab } from './components/workspace/TeamTab';
import { TraceabilityTab } from './components/workspace/TraceabilityTab';
import { ChangeImpactTab } from './components/workspace/ChangeImpactTab';
import { ReportsTab } from './components/workspace/ReportsTab';
import { EvaluationTab } from './components/workspace/EvaluationTab';

// Modals
import { NewProjectModal } from './components/modals/NewProjectModal';
import { SettingsModal } from './components/modals/SettingsModal';
import { AnalysisProgressModal } from './components/modals/AnalysisProgressModal';

// Toast
import { CheckCircle2, AlertCircle, Info } from 'lucide-react';

const WorkspaceContent: React.FC = () => {
  const { activeTab, toast } = useApp();
  const [isNewProjectOpen, setIsNewProjectOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isAnalysisOpen, setIsAnalysisOpen] = useState(false);

  const renderActiveTab = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'sources':
        return <SourcesTab />;
      case 'requirements':
        return <RequirementsTab />;
      case 'issues':
        return <IssuesTab />;
      case 'clarifications':
        return <ClarificationsTab />;
      case 'architecture':
        return <ArchitectureTab />;
      case 'planning':
        return <PlanningTab />;
      case 'team':
        return <TeamTab />;
      case 'traceability':
        return <TraceabilityTab />;
      case 'change_impact':
        return <ChangeImpactTab />;
      case 'reports':
        return <ReportsTab />;
      case 'evaluation':
        return <EvaluationTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Navigation */}
      <Navbar
        onOpenNewProject={() => setIsNewProjectOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onRunAnalysis={() => setIsAnalysisOpen(true)}
      />

      {/* Project Header Overview */}
      <ProjectHeader />

      {/* 12-Tab Navigation Bar */}
      <TabNavigation />

      {/* Main Tabbed Workspace Canvas */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {renderActiveTab()}
      </main>

      {/* Global Modals */}
      <NewProjectModal isOpen={isNewProjectOpen} onClose={() => setIsNewProjectOpen(false)} />
      <SettingsModal isOpen={isSettingsOpen} onClose={() => setIsSettingsOpen(false)} />
      <AnalysisProgressModal isOpen={isAnalysisOpen} onClose={() => setIsAnalysisOpen(false)} />

      {/* Global Toast Notification */}
      {toast && (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-3 fade-in duration-200">
          <div
            className={`glass-panel px-4 py-3 rounded-2xl shadow-2xl flex items-center space-x-3 border ${
              toast.type === 'success'
                ? 'border-emerald-600/60 bg-emerald-950/90 text-emerald-200'
                : toast.type === 'error'
                ? 'border-red-600/60 bg-red-950/90 text-red-200'
                : 'border-indigo-600/60 bg-slate-900/95 text-slate-200'
            }`}
          >
            {toast.type === 'success' && <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />}
            {toast.type === 'error' && <AlertCircle className="h-5 w-5 text-red-400 shrink-0" />}
            {toast.type === 'info' && <Info className="h-5 w-5 text-indigo-400 shrink-0" />}
            <span className="text-xs font-semibold">{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default function App() {
  return (
    <AppProvider>
      <WorkspaceContent />
    </AppProvider>
  );
}
