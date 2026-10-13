import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { EvaluationResult } from '../../types';
import {
  BarChart3, Play, CheckCircle2, ShieldAlert,
  TrendingUp, Activity
} from 'lucide-react';

export const EvaluationTab: React.FC = () => {
  const [evalResult, setEvalResult] = useState<EvaluationResult | null>(null);
  const [isRunning, setIsRunning] = useState(false);

  const loadEvaluation = async () => {
    setIsRunning(true);
    try {
      const data = await api.runEvaluation();
      setEvalResult(data);
    } catch (e) {
      console.error('Error running evaluation benchmarks', e);
    } finally {
      setIsRunning(false);
    }
  };

  useEffect(() => {
    loadEvaluation();
  }, []);

  const formatRate = (value: number) => `${(value * 100).toFixed(1)}%`;

  const hasBenchmark = (metric: {
    total_samples: number;
  }) => metric.total_samples > 0;

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="glass-panel p-4 rounded-2xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <BarChart3 className="h-5 w-5" />
          </div>

          <div>
            <h3 className="text-sm font-bold text-white">
              Empirical Evaluation & Reproducible Benchmark Suite
            </h3>

            <p className="text-xs text-slate-400">
              Results are computed from the currently available benchmark cases.
              Metrics without ground-truth data are explicitly marked as not evaluated.
            </p>
          </div>
        </div>

        <button
          onClick={loadEvaluation}
          disabled={isRunning}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-xl text-xs font-semibold flex items-center space-x-2 transition-all shadow-md shadow-indigo-600/30 disabled:opacity-50"
        >
          <Play className={`h-3.5 w-3.5 fill-white ${isRunning ? 'animate-spin' : ''}`} />
          <span>{isRunning ? 'Running Benchmark Suite...' : 'Re-Run Evaluation Suite'}</span>
        </button>
      </div>

      {evalResult && (
        <>
          {/* Benchmark Scope Notice */}
          <div className="glass-panel p-4 rounded-2xl border border-amber-500/20 bg-amber-950/10">
            <div className="flex items-start space-x-3">
              <ShieldAlert className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />

              <div>
                <h4 className="text-sm font-bold text-amber-300">
                  Benchmark Scope & Interpretation
                </h4>

                <p className="text-xs text-slate-400 mt-1 leading-relaxed">
                  The current reproducible benchmark contains positive examples for
                  ambiguity, conflict, and duplicate detection. These results represent
                  positive-case detection rates, not conventional classification
                  precision/recall/F1 measurements. Requirement extraction,
                  independently measured traceability coverage, hallucination rate,
                  latency, and external baselines are not currently benchmarked.
                </p>
              </div>
            </div>
          </div>

          {/* Top Score Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">

            {/* Requirement Extraction */}
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400">
                  Requirement Extraction
                </span>

                <span className="text-[10px] uppercase font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded">
                  Not Evaluated
                </span>
              </div>

              <div className="text-2xl font-black text-slate-500">
                N/A
              </div>

              <p className="text-[11px] text-slate-500">
                No extraction ground-truth dataset is currently included.
              </p>
            </div>

            {/* Conflict Detection */}
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400">
                  Conflict Detection
                </span>

                <span className="text-[10px] uppercase font-bold text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded">
                  Positive Cases
                </span>
              </div>

              <div className="text-2xl font-black text-emerald-400">
                {hasBenchmark(evalResult.conflict_detection)
                  ? formatRate(evalResult.conflict_detection.f1_score)
                  : 'N/A'}
              </div>

              <p className="text-[11px] text-slate-500">
                {evalResult.conflict_detection.total_samples} positive cases detected out of{' '}
                {evalResult.conflict_detection.total_samples}.
              </p>
            </div>

            {/* Ambiguity Detection */}
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400">
                  Ambiguity Detection
                </span>

                <span className="text-[10px] uppercase font-bold text-purple-400 bg-purple-950/80 px-2 py-0.5 rounded">
                  Positive Cases
                </span>
              </div>

              <div className="text-2xl font-black text-purple-400">
                {hasBenchmark(evalResult.ambiguity_detection)
                  ? formatRate(evalResult.ambiguity_detection.f1_score)
                  : 'N/A'}
              </div>

              <p className="text-[11px] text-slate-500">
                {evalResult.ambiguity_detection.total_samples} positive cases detected out of{' '}
                {evalResult.ambiguity_detection.total_samples}.
              </p>
            </div>

            {/* Duplicate Detection */}
            <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-400">
                  Duplicate Detection
                </span>

                <span className="text-[10px] uppercase font-bold text-blue-400 bg-blue-950/80 px-2 py-0.5 rounded">
                  Positive Cases
                </span>
              </div>

              <div className="text-2xl font-black text-blue-400">
                {hasBenchmark(evalResult.duplicate_detection)
                  ? formatRate(evalResult.duplicate_detection.f1_score)
                  : 'N/A'}
              </div>

              <p className="text-[11px] text-slate-500">
                {evalResult.duplicate_detection.total_samples} positive case detected out of{' '}
                {evalResult.duplicate_detection.total_samples}.
              </p>
            </div>
          </div>

          {/* Benchmark Results */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div>
              <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                <span>Reproducible Benchmark Results</span>
              </h4>

              <p className="text-xs text-slate-400 mt-0.5">
                Detection performance on the currently available positive benchmark cases.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900 border-b border-slate-800 text-[11px] uppercase font-bold text-slate-400">
                  <tr>
                    <th className="p-3">Capability</th>
                    <th className="p-3 text-center">Benchmark Cases</th>
                    <th className="p-3 text-center">Detected</th>
                    <th className="p-3 text-center">Detection Rate</th>
                    <th className="p-3">Interpretation</th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-slate-800/80">

                  <tr className="hover:bg-slate-900/40">
                    <td className="p-3 text-white font-semibold">
                      Ambiguity Detection
                    </td>

                    <td className="p-3 text-center font-mono text-slate-300">
                      {evalResult.ambiguity_detection.total_samples}
                    </td>

                    <td className="p-3 text-center font-mono text-emerald-400">
                      {Math.round(
                        evalResult.ambiguity_detection.f1_score *
                        evalResult.ambiguity_detection.total_samples
                      )}
                    </td>

                    <td className="p-3 text-center font-mono font-bold text-purple-400">
                      {formatRate(evalResult.ambiguity_detection.f1_score)}
                    </td>

                    <td className="p-3 text-slate-400">
                      Positive benchmark cases detected successfully.
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="p-3 text-white font-semibold">
                      Conflict Detection
                    </td>

                    <td className="p-3 text-center font-mono text-slate-300">
                      {evalResult.conflict_detection.total_samples}
                    </td>

                    <td className="p-3 text-center font-mono text-emerald-400">
                      {Math.round(
                        evalResult.conflict_detection.f1_score *
                        evalResult.conflict_detection.total_samples
                      )}
                    </td>

                    <td className="p-3 text-center font-mono font-bold text-emerald-400">
                      {formatRate(evalResult.conflict_detection.f1_score)}
                    </td>

                    <td className="p-3 text-slate-400">
                      Positive contradiction cases detected successfully.
                    </td>
                  </tr>

                  <tr className="hover:bg-slate-900/40">
                    <td className="p-3 text-white font-semibold">
                      Duplicate Detection
                    </td>

                    <td className="p-3 text-center font-mono text-slate-300">
                      {evalResult.duplicate_detection.total_samples}
                    </td>

                    <td className="p-3 text-center font-mono text-emerald-400">
                      {Math.round(
                        evalResult.duplicate_detection.f1_score *
                        evalResult.duplicate_detection.total_samples
                      )}
                    </td>

                    <td className="p-3 text-center font-mono font-bold text-blue-400">
                      {formatRate(evalResult.duplicate_detection.f1_score)}
                    </td>

                    <td className="p-3 text-slate-400">
                      Positive duplicate case detected successfully.
                    </td>
                  </tr>

                </tbody>
              </table>
            </div>
          </div>

          {/* Evidence / Limitations */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <h4 className="text-sm font-bold text-white flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-blue-400" />
              <span>Evaluation Coverage & Limitations</span>
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">

              <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
                <span className="font-bold text-slate-200 block">
                  Requirement Extraction
                </span>

                <p className="text-slate-500 mt-2 leading-relaxed">
                  Not independently evaluated because the current benchmark does not
                  provide annotated extraction ground truth.
                </p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
                <span className="font-bold text-slate-200 block">
                  Traceability Coverage
                </span>

                <p className="text-slate-500 mt-2 leading-relaxed">
                  The current endpoint does not independently validate traceability
                  against an external ground-truth dataset.
                </p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
                <span className="font-bold text-slate-200 block">
                  Baseline Comparison
                </span>

                <p className="text-slate-500 mt-2 leading-relaxed">
                  No independently implemented baseline systems are currently included
                  in the reproducible evaluation.
                </p>
              </div>

              <div className="bg-slate-900/90 border border-slate-800 p-4 rounded-xl">
                <span className="font-bold text-slate-200 block">
                  Ablation Studies
                </span>

                <p className="text-slate-500 mt-2 leading-relaxed">
                  Ablation results are not reported because controlled component-removal
                  experiments have not yet been executed.
                </p>
              </div>

            </div>
          </div>

          {/* Current Run */}
          <div className="glass-panel p-4 rounded-2xl border border-slate-800">
            <div className="flex items-center space-x-2 text-xs text-slate-500">
              <Activity className="h-4 w-4" />
              <span>
                Benchmark execution completed at{' '}
                {new Date(evalResult.tested_at).toLocaleString()}
              </span>
            </div>
          </div>
        </>
      )}
    </div>
  );
};