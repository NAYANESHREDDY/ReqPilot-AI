import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { Settings, Key, ShieldCheck, Cpu, X, Check } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const { apiKey, setApiKey, provider, setProvider, showToast } = useApp();
  const [tempKey, setTempKey] = useState(apiKey);
  const [tempProvider, setTempProvider] = useState(provider);

  if (!isOpen) return null;

  const handleSave = () => {
    setApiKey(tempKey);
    setProvider(tempProvider);
    showToast('AI engine settings saved!', 'success');
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Settings className="h-4 w-4" />
            </div>
            <h3 className="text-base font-bold text-white">AI Engine & Provider Settings</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-lg">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* Provider Selector */}
          <div>
            <label className="block text-slate-400 mb-1.5 font-semibold">Inference Model Provider</label>
            <div className="grid grid-cols-4 gap-2">
              <button
                type="button"
                onClick={() => setTempProvider('offline')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  tempProvider === 'offline'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <div className="font-bold text-xs">Offline Semantic</div>
                <div className="text-[10px] text-slate-500 mt-1">Zero config, 100% private</div>
              </button>

              <button
                type="button"
                onClick={() => setTempProvider('groq')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  tempProvider === 'groq'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <div className="font-bold text-xs">Groq</div>
                <div className="text-[10px] text-slate-500 mt-1">Llama 3.3 70B, very fast</div>
              </button>

              <button
                type="button"
                onClick={() => setTempProvider('gemini')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  tempProvider === 'gemini'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <div className="font-bold text-xs">Google Gemini</div>
                <div className="text-[10px] text-slate-500 mt-1">Gemini 1.5 Flash / Pro</div>
              </button>

              <button
                type="button"
                onClick={() => setTempProvider('openai')}
                className={`p-3 rounded-xl border text-left transition-all ${
                  tempProvider === 'openai'
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-md'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                <div className="font-bold text-xs">OpenAI</div>
                <div className="text-[10px] text-slate-500 mt-1">GPT-4o / Mini</div>
              </button>
            </div>
          </div>

          {/* API Key Input (if provider requires key) */}
          {tempProvider !== 'offline' && (
            <div>
              <label className="block text-slate-400 mb-1 font-semibold flex items-center space-x-1.5">
                <Key className="h-3.5 w-3.5 text-indigo-400" />
                <span>
                  {tempProvider === 'gemini'
                    ? 'Google Gemini API Key'
                    : tempProvider === 'groq'
                    ? 'Groq API Key'
                    : 'OpenAI API Key'}
                </span>
              </label>
              <input
                type="password"
                placeholder="Paste API key here (saved locally in your browser session)..."
                value={tempKey}
                onChange={(e) => setTempKey(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
              />
              <p className="text-[11px] text-slate-500 mt-1">
                If omitted, ReqPilot AI automatically uses its high-accuracy deterministic semantic engine.
              </p>
            </div>
          )}

          {/* Prompt Injection Defense Guarantee */}
          <div className="bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 space-y-1">
            <div className="flex items-center space-x-2 text-indigo-300 font-bold">
              <ShieldCheck className="h-4 w-4" />
              <span>Prompt Injection Defense (Section 39)</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              All uploaded client requirement text is strictly isolated in untrusted data delimiters and filtered before agent ingestion to prevent prompt injection and unauthorized system execution.
            </p>
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-2 border-t border-slate-800">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-800 text-slate-300 hover:bg-slate-700"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 text-white hover:bg-indigo-500 shadow-md shadow-indigo-600/30 flex items-center space-x-1.5"
          >
            <Check className="h-3.5 w-3.5" />
            <span>Save Settings</span>
          </button>
        </div>
      </div>
    </div>
  );
};
