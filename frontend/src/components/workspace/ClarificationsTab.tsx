import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { api } from '../../services/api';
import { ClarificationQuestion } from '../../types';
import { HelpCircle, CheckCircle2, Clock, Send, MessageSquare, Sparkles } from 'lucide-react';

export const ClarificationsTab: React.FC = () => {
  const { activeProject, refreshStats, showToast } = useApp();
  const [clarifications, setClarifications] = useState<ClarificationQuestion[]>([]);
  const [customAnswers, setCustomAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<string | null>(null);

  const loadClarifications = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getClarifications(activeProject.id);
      setClarifications(data);
    } catch (e) {
      console.error('Error loading clarifications', e);
    }
  };

  useEffect(() => {
    loadClarifications();
  }, [activeProject]);

  const handleSelectOption = (questionId: string, optionText: string) => {
    setCustomAnswers((prev) => ({ ...prev, [questionId]: optionText }));
  };

  const submitAnswer = async (question: ClarificationQuestion) => {
    const answerText = customAnswers[question.id] || question.suggested_options[0];
    if (!answerText) {
      showToast('Please type an answer or select a suggested option', 'error');
      return;
    }

    setIsSubmitting(question.id);
    try {
      await api.answerClarification(question.id, answerText, true);
      showToast(`Answer applied! Requirement ${question.requirement_id || ''} updated to version baseline.`, 'success');
      await loadClarifications();
      await refreshStats();
    } catch (e) {
      showToast('Failed to submit clarification answer', 'error');
    } finally {
      setIsSubmitting(null);
    }
  };

  const pendingQuestions = clarifications.filter((q) => q.status === 'pending');
  const answeredQuestions = clarifications.filter((q) => q.status === 'answered');

  return (
    <div className="space-y-6">
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
        <div className="flex items-center space-x-2">
          <HelpCircle className="h-5 w-5 text-indigo-400" />
          <h3 className="text-base font-bold text-white">Stakeholder Clarification Workflow (Section 8.8)</h3>
        </div>
        <p className="text-xs text-slate-400 max-w-3xl leading-relaxed">
          The Clarification Agent converts detected ambiguities, missing boundaries, and conflicting policies into actionable stakeholder questionnaires. Answering updates the requirement baseline and increments version numbers automatically.
        </p>
      </div>

      {/* Pending Question Cards */}
      <div className="space-y-4">
        <h4 className="text-sm font-bold text-white flex items-center space-x-2">
          <Clock className="h-4 w-4 text-amber-400" />
          <span>Pending Inquiries ({pendingQuestions.length})</span>
        </h4>

        {pendingQuestions.length === 0 ? (
          <div className="glass-panel p-8 text-center rounded-2xl border border-slate-800 text-slate-400">
            <CheckCircle2 className="h-7 w-7 mx-auto text-emerald-400 mb-1" />
            <p className="text-xs font-semibold">No pending questions! All stakeholder inquiries resolved.</p>
          </div>
        ) : (
          pendingQuestions.map((q) => {
            const currentAnswer = customAnswers[q.id] || '';

            return (
              <div
                key={q.id}
                className="glass-panel rounded-2xl border border-slate-800 hover:border-slate-700 p-5 space-y-4 transition-all"
              >
                {/* Header Row */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                        q.priority === 'high'
                          ? 'bg-red-950/80 border-red-800/80 text-red-300'
                          : 'bg-slate-800 border-slate-700 text-slate-300'
                      }`}
                    >
                      {q.priority} Priority
                    </span>
                    {q.requirement_id && (
                      <span className="font-mono text-xs font-bold text-indigo-300 bg-indigo-950/60 border border-indigo-800/60 px-2 py-0.5 rounded-lg">
                        {q.requirement_id}
                      </span>
                    )}
                  </div>
                  <span className="text-[11px] text-amber-400 flex items-center font-semibold">
                    <Clock className="h-3 w-3 mr-1" />
                    Needs Decision
                  </span>
                </div>

                {/* Question & Rationale */}
                <div className="space-y-1">
                  <h4 className="text-sm font-bold text-white">{q.question}</h4>
                  <p className="text-xs text-slate-400 italic">Why this is asked: {q.rationale}</p>
                </div>

                {/* Suggested Options */}
                {q.suggested_options && q.suggested_options.length > 0 && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                      Suggested Standard Answers (Click to select):
                    </span>
                    <div className="flex flex-wrap gap-2">
                      {q.suggested_options.map((opt, i) => (
                        <button
                          key={i}
                          onClick={() => handleSelectOption(q.id, opt)}
                          className={`text-left text-xs px-3 py-1.5 rounded-xl border transition-all ${
                            currentAnswer === opt
                              ? 'bg-indigo-600/30 border-indigo-500 text-white font-medium shadow-md shadow-indigo-950'
                              : 'bg-slate-900/80 border-slate-700/80 text-slate-300 hover:border-slate-600'
                          }`}
                        >
                          {opt}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Answer Input & Submit */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 pt-2 border-t border-slate-800">
                  <input
                    type="text"
                    placeholder="Type or customize stakeholder resolution..."
                    value={currentAnswer}
                    onChange={(e) => setCustomAnswers({ ...customAnswers, [q.id]: e.target.value })}
                    className="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                  />
                  <button
                    onClick={() => submitAnswer(q)}
                    disabled={isSubmitting === q.id}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
                  >
                    <Send className="h-3.5 w-3.5" />
                    <span>{isSubmitting === q.id ? 'Applying...' : 'Apply & Update Baseline'}</span>
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Answered / Resolved Questions */}
      {answeredQuestions.length > 0 && (
        <div className="space-y-3 pt-4 border-t border-slate-800">
          <h4 className="text-sm font-bold text-white flex items-center space-x-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" />
            <span>Answered Decisions ({answeredQuestions.length})</span>
          </h4>

          <div className="space-y-2">
            {answeredQuestions.map((q) => (
              <div
                key={q.id}
                className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-xl space-y-1.5 opacity-80"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">{q.question}</span>
                  <span className="font-mono text-[10px] text-indigo-300 bg-indigo-950/60 px-2 py-0.5 rounded">
                    {q.requirement_id}
                  </span>
                </div>
                <div className="text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/40 p-2 rounded-lg font-medium">
                  Decision Applied: "{q.answer}"
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
