import csv, json
from pathlib import Path
import sys
sys.path.append('evaluation/multi_project/scripts')
from scorer import score_run

run_mappings = {
    'ev_charging': 'ev_charging_run_1c57d2e2',
    'ecommerce_platform': 'ecommerce_platform_run_1e2d6f1a',
    'banking_management': 'banking_management_run_ba26cb8e',
    'library_management': 'library_management_run_037fa230'
}

archived_mappings = {
    'hospital_management': 'hospital_management_run_4046c3ca'
}

all_reports = {}
summary_rows = []

for dkey, rdir_name in run_mappings.items():
    rdir = Path('evaluation/multi_project/runs') / rdir_name
    gold = Path('evaluation/multi_project/benchmark') / dkey / 'gold_reference.json'
    
    report = score_run(rdir, gold)
    all_reports[dkey] = report
    
    ce = report['classification_evaluation']
    ms = report['matching_summary']
    si = report['structural_integrity']
    
    rep_md = '# Evaluation Report: ' + report['project_title'] + ' (' + dkey + ')\n\n'
    rep_md += '## Run Information\n'
    rep_md += '- **Run ID**: ' + report['run_id'] + '\n'
    rep_md += '- **Timestamp**: ' + report['timestamp'] + '\n'
    rep_md += '- **Provider / Model**: ' + report['provider'] + ' / ' + report['model'] + '\n'
    rep_md += '- **LLM Extraction Succeeded**: ' + str(report['llm_extraction_succeeded']) + '\n'
    rep_md += '- **Deterministic Fallback Used**: ' + str(report['fallback_used']) + '\n\n'
    
    rep_md += '## Content-Grounded Requirement Matching\n'
    rep_md += '- **Predicted Requirements**: ' + str(ms['predicted_requirements_count']) + '\n'
    rep_md += '- **Reference Requirements**: ' + str(ms['reference_requirements_count']) + '\n'
    rep_md += '- **Uniquely Matched Pairs**: ' + str(ms['uniquely_matched_count']) + '\n'
    rep_md += '- **Unmatched Predictions**: ' + str(ms['unmatched_predictions_count']) + '\n'
    rep_md += '- **Ambiguous Predictions**: ' + str(ms['ambiguous_predictions_count']) + '\n'
    rep_md += '- **Duplicate Gold Matches**: ' + str(ms['duplicate_gold_matches_count']) + '\n'
    rep_md += '- **Unmatched Reference Entries**: ' + str(ms['unmatched_reference_count']) + '\n\n'
    
    rep_md += '## Semantic Classification Metrics (On Matched Requirements)\n'
    rep_md += '- **Matched Denominator**: ' + str(ce['valid_matched_denominator']) + '\n'
    rep_md += '- **Correct Classifications**: ' + str(ce['correct_classifications']) + '\n'
    rep_md += '- **Accuracy**: ' + str(round(ce['accuracy'] * 100, 2)) + '%\n'
    rep_md += '- **Macro Precision**: ' + str(ce['macro_precision']) + '\n'
    rep_md += '- **Macro Recall**: ' + str(ce['macro_recall']) + '\n'
    rep_md += '- **Macro F1**: ' + str(ce['macro_f1']) + '\n\n'
    
    rep_md += '### Per-Module Breakdown\n'
    rep_md += '| Module | TP | FP | FN | Precision | Recall | F1 |\n'
    rep_md += '|---|---|---|---|---|---|---|\n'
    for cls, m in ce['per_class_metrics'].items():
        rep_md += '| ' + cls + ' | ' + str(m['tp']) + ' | ' + str(m['fp']) + ' | ' + str(m['fn']) + ' | ' + str(m['precision']) + ' | ' + str(m['recall']) + ' | ' + str(m['f1']) + ' |\n'
        
    rep_md += '\n### Classification Errors (' + str(ce['total_errors']) + ' total)\n'
    for err in ce['errors_sample']:
        rep_md += '- **' + err['pred_id'] + ' -> ' + err['gold_id'] + '** (' + err['summary'][:50] + '...): Expected ' + err['expected'] + ', Predicted ' + err['predicted'] + '\n'
        
    rep_md += '\n## Structural Integrity Checks\n'
    rep_md += '- **Total Requirements**: ' + str(si['total_requirements']) + '\n'
    rep_md += '- **Requirements with Assigned Tasks**: ' + str(si['requirements_with_tasks']) + ' (' + str(si['task_coverage_pct']) + '%)\n'
    rep_md += '- **Total Modules**: ' + str(si['total_modules']) + '\n'
    rep_md += '- **Total Architecture Relations**: ' + str(si['total_relations']) + '\n'
    rep_md += '- **Total Test Cases**: ' + str(si['total_test_cases']) + '\n'
    rep_md += '- **Untested Requirements**: ' + str(si['untested_requirements_count']) + '\n\n'
    
    rep_md += '## Declared Non-Evaluated Metrics\n'
    for item in report['unsupported_metrics_declared']:
        rep_md += '- ' + item + '\n'
        
    Path('evaluation/multi_project/reports/' + dkey + '_report.md').write_text(rep_md, encoding='utf-8')
    print('Updated report for ' + dkey)
    
    summary_rows.append({
        'domain': dkey,
        'project_title': report['project_title'],
        'run_id': report['run_id'][:8],
        'llm_succeeded': report['llm_extraction_succeeded'],
        'fallback_used': report['fallback_used'],
        'pred_reqs': ms['predicted_requirements_count'],
        'gold_reqs': ms['reference_requirements_count'],
        'matched': ms['uniquely_matched_count'],
        'unmatched_pred': ms['unmatched_predictions_count'],
        'correct': ce['correct_classifications'],
        'accuracy': ce['accuracy'],
        'macro_precision': ce['macro_precision'],
        'macro_recall': ce['macro_recall'],
        'macro_f1': ce['macro_f1'],
        'task_coverage_pct': si['task_coverage_pct'],
        'total_modules': si['total_modules'],
        'total_relations': si['total_relations']
    })

Path('evaluation/multi_project/results/summary.json').write_text(json.dumps(all_reports, indent=2), encoding='utf-8')

with open('evaluation/multi_project/results/summary.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=summary_rows[0].keys())
    writer.writeheader()
    writer.writerows(summary_rows)

print('Updated summary.json and summary.csv successfully!')
