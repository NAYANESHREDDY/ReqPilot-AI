import React, { createContext, useContext, useState, useEffect } from 'react';
import { Project, ProjectStats } from '../types';
import { api } from '../services/api';

interface AppContextType {
  projects: Project[];
  activeProject: Project | null;
  setActiveProject: (p: Project) => void;
  stats: ProjectStats | null;
  refreshStats: () => Promise<void>;
  refreshProjects: () => Promise<void>;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  apiKey: string;
  setApiKey: (key: string) => void;
  provider: string;
  setProvider: (p: string) => void;
  isAnalyzing: boolean;
  setIsAnalyzing: (v: boolean) => void;
  toast: { message: string; type: 'success' | 'error' | 'info' } | null;
  showToast: (message: string, type?: 'success' | 'error' | 'info') => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [apiKey, setApiKey] = useState<string>(() => localStorage.getItem('reqpilot_api_key') || '');
  const [provider, setProvider] = useState<string>(() => localStorage.getItem('reqpilot_provider') || 'gemini');
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  const showToast = (message: string, type: 'success' | 'error' | 'info' = 'info') => {
    setToast({ message, type });
    setTimeout(() => {
      setToast(null);
    }, 4000);
  };

  const refreshProjects = async () => {
    try {
      const data = await api.getProjects();
      setProjects(data);
      if (data.length > 0 && !activeProject) {
        setActiveProject(data[0]);
      }
    } catch (e) {
      console.error('Failed to load projects', e);
    }
  };

  const refreshStats = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getProjectStats(activeProject.id);
      setStats(data);
    } catch (e) {
      console.error('Failed to load stats', e);
    }
  };

  useEffect(() => {
    refreshProjects();
  }, []);

  useEffect(() => {
    if (activeProject) {
      refreshStats();
    }
  }, [activeProject]);

  useEffect(() => {
    localStorage.setItem('reqpilot_api_key', apiKey);
  }, [apiKey]);

  useEffect(() => {
    localStorage.setItem('reqpilot_provider', provider);
  }, [provider]);

  return (
    <AppContext.Provider
      value={{
        projects,
        activeProject,
        setActiveProject,
        stats,
        refreshStats,
        refreshProjects,
        activeTab,
        setActiveTab,
        apiKey,
        setApiKey,
        provider,
        setProvider,
        isAnalyzing,
        setIsAnalyzing,
        toast,
        showToast,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
