# ReqPilot Grounded Multi-Project Semantic Scorer
# Version 3.0 - Globally Consistent Exact-Precedence Anchor Matching

import re
import json
from pathlib import Path
from collections import Counter

CANONICAL_MODULE_MAP = {
    'AUTHENTICATION': ['Authentication & Authorization', 'Authentication', 'Security & Access Control', 'Security'],
    'CHARGING-STATION': ['Charging Station Management', 'Charging Station'],
    'BOOKING': ['Booking & Scheduling', 'Booking', 'Reservation'],
    'CHARGING-SESSION': ['Charging Session Management', 'Charging Session'],
    'NOTIFICATION': ['Notification Service', 'Notifications & Communication', 'Notifications'],
    'MAINTENANCE': ['Maintenance Management', 'Maintenance'],
    'DATA': ['Application Data Store', 'Data Management', 'Core Storage'],
    'REPORTING': ['Reporting & Analytics', 'Reports', 'Analytics'],
    'PAYMENT': ['Payment Management', 'Billing and Payment', 'Payments'],
    'GATEWAY': ['API Gateway', 'System Gateway'],
    'SEARCH': ['Search & Discovery', 'Search'],
    'PROFILE': ['Profile Management', 'User Profile'],
    'FILE': ['File & Document Management', 'Document Management'],
    'DEPARTMENT': ['Department']
}

def canonicalize(module_name):
    if not module_name:
        return 'UNASSIGNED'
    name_clean = module_name.strip().upper()
    for canon, variants in CANONICAL_MODULE_MAP.items():
        if name_clean == canon:
            return canon
        for v in variants:
            if name_clean == v.upper() or v.upper() in name_clean:
                return canon
    return name_clean

def normalize_text(text):
    if not text:
        return ''
    t = text.lower()
    # Strip any leading section header ending in requirements, management, administration, notifications, auditing, security
    # Guard with positive lookahead to require a requirement actor/subject directly following
    header_strip = r'^[a-z\s,]+?\s+(?:requirements|management|administration|notifications|auditing|security)\s+(?=(?:customers|drivers|station|vendors|warehouse|support|tellers|loan|patrons|circulation|catalogers|administrators|maintenance|the\s+system)\b)'
    t = re.sub(header_strip, '', t)
    t = re.sub(r'^(the\s+system\s+shall|the\s+system\s+should)\s+', '', t)
    t = re.sub(r'[^\w\s]', ' ', t)
    return re.sub(r'\s+', ' ', t).strip()

def is_exact_or_clean_header_match(pt, gt):
    if not pt or not gt or len(pt) < 15 or len(gt) < 15:
        return False
    if pt == gt:
        return True
    if pt.endswith(gt):
        prefix = pt[:-len(gt)].strip()
        forbidden_verbs = ['warning', 'popup', 'before', 'after', 'expire', 'when', 'shall', 'should', 'prevent', 'display', 'alert']
        if len(prefix) <= 45 and not any(w in prefix for w in forbidden_verbs):
            return True
    return False

def compute_similarity(s1, s2):
    if not s1 or not s2 or len(s1) < 15 or len(s2) < 15:
        return 0.0
    if is_exact_or_clean_header_match(s1, s2) or is_exact_or_clean_header_match(s2, s1):
        return 1.0
    # Guard against context embedding: if s1 in s2 or s2 in s1, require strict length ratio
    if s1 in s2 or s2 in s1:
        ratio = min(len(s1), len(s2)) / max(len(s1), len(s2))
        if ratio < 0.85:
            return 0.0
        return ratio
    # Token Jaccard
    w1, w2 = set(s1.split()), set(s2.split())
    if not w1 or not w2:
        return 0.0
    jacc = len(w1 & w2) / len(w1 | w2)
    return jacc if jacc >= 0.85 else 0.0

def match_prediction_to_gold(pred_req, gold_details):
    """
    Evaluates candidates for a single prediction against gold details.
    Exact matches take strict precedence over partial matches.
    Guards against context-embedding false positives.
    """
    pred_texts = [
        normalize_text(pred_req.get('source_excerpt')),
        normalize_text(pred_req.get('description')),
        normalize_text(pred_req.get('summary'))
    ]
    pred_texts = [t for t in pred_texts if t and len(t) >= 15]
    if not pred_texts:
        return None, 'UNMATCHED'

    tier1_candidates = []
    tier2_candidates = []

    for gid, ginfo in gold_details.items():
        gold_texts = [
            normalize_text(ginfo.get('statement')),
            normalize_text(ginfo.get('summary'))
        ]
        gold_texts = [t for t in gold_texts if t and len(t) >= 15]

        is_tier1 = False
        best_sim = 0.0
        for pt in pred_texts:
            for gt in gold_texts:
                if is_exact_or_clean_header_match(pt, gt) or is_exact_or_clean_header_match(gt, pt):
                    is_tier1 = True
                    break
                sim = compute_similarity(pt, gt)
                if sim > best_sim:
                    best_sim = sim
            if is_tier1:
                break

        if is_tier1:
            tier1_candidates.append(gid)
        elif best_sim >= 0.85:
            tier2_candidates.append(gid)

    if len(tier1_candidates) == 1:
        return tier1_candidates[0], 'UNIQUE_MATCH'
    elif len(tier1_candidates) > 1:
        return None, 'AMBIGUOUS_MATCH'

    if len(tier2_candidates) == 1:
        return tier2_candidates[0], 'UNIQUE_MATCH'
    elif len(tier2_candidates) > 1:
        return None, 'AMBIGUOUS_MATCH'

    return None, 'UNMATCHED'

def global_match_requirements(predictions, gold_details):
    """
    Globally consistent one-to-one assignment independent of prediction ordering.
    Exact matches (Tier 1) take strict precedence over partial matches (Tier 2).
    """
    pred_info = {}
    for p in predictions:
        pid = p.get('id', '')
        p_texts = [
            normalize_text(p.get('source_excerpt')),
            normalize_text(p.get('description')),
            normalize_text(p.get('summary'))
        ]
        pred_info[pid] = {
            'req': p,
            'texts': [t for t in p_texts if t and len(t) >= 15]
        }

    gold_info = {}
    for gid, g in gold_details.items():
        g_texts = [
            normalize_text(g.get('statement')),
            normalize_text(g.get('summary'))
        ]
        gold_info[gid] = {
            'gold': g,
            'texts': [t for t in g_texts if t and len(t) >= 15]
        }

    tier1_edges = []
    tier2_edges = []

    for pid, pdata in pred_info.items():
        for gid, gdata in gold_info.items():
            best_score = 0.0
            is_tier1 = False
            for pt in pdata['texts']:
                for gt in gdata['texts']:
                    if is_exact_or_clean_header_match(pt, gt) or is_exact_or_clean_header_match(gt, pt):
                        is_tier1 = True
                        best_score = 1.0
                        break
                    sim = compute_similarity(pt, gt)
                    if sim > best_score:
                        best_score = sim
                if is_tier1:
                    break
            
            if is_tier1:
                tier1_edges.append((pid, gid, 1.0))
            elif best_score >= 0.85:
                tier2_edges.append((pid, gid, best_score))

    matched_pairs = []
    assigned_pred = set()
    assigned_gold = set()
    ambiguous_preds = set()
    duplicate_gold_matches = []

    # Deterministic order by PID
    sorted_pids = sorted(pred_info.keys())

    # Phase 1: Resolve Tier 1 (Exact Matches)
    pred_tier1_map = {}
    gold_tier1_map = {}
    for pid, gid, score in tier1_edges:
        pred_tier1_map.setdefault(pid, []).append(gid)
        gold_tier1_map.setdefault(gid, []).append(pid)

    for pid in sorted_pids:
        cands = pred_tier1_map.get(pid, [])
        if len(cands) > 1:
            ambiguous_preds.add(pid)

    for gid in sorted(gold_tier1_map.keys()):
        pids = sorted(gold_tier1_map[gid])
        eligible = [p for p in pids if p not in ambiguous_preds]
        if eligible:
            chosen_pid = eligible[0]
            if chosen_pid not in assigned_pred and gid not in assigned_gold:
                assigned_pred.add(chosen_pid)
                assigned_gold.add(gid)
                matched_pairs.append({
                    'pred_id': chosen_pid,
                    'gold_id': gid,
                    'match_type': 'EXACT'
                })
            for dup_pid in eligible[1:]:
                duplicate_gold_matches.append({'pred_id': dup_pid, 'gold_id': gid})

    # Phase 2: Resolve Tier 2 (High-Fidelity Partial Matches >= 0.85)
    remaining_tier2 = [
        (pid, gid, score) for pid, gid, score in tier2_edges
        if pid not in assigned_pred and gid not in assigned_gold and pid not in ambiguous_preds
    ]

    pred_tier2_map = {}
    gold_tier2_map = {}
    for pid, gid, score in remaining_tier2:
        pred_tier2_map.setdefault(pid, []).append((gid, score))
        gold_tier2_map.setdefault(gid, []).append((pid, score))

    for pid in sorted_pids:
        if pid in assigned_pred or pid in ambiguous_preds:
            continue
        cands = pred_tier2_map.get(pid, [])
        if len(cands) > 1:
            ambiguous_preds.add(pid)

    for gid in sorted(gold_tier2_map.keys()):
        if gid in assigned_gold:
            continue
        cands = gold_tier2_map[gid]
        eligible_pids = sorted([p for p, s in cands if p not in ambiguous_preds and p not in assigned_pred])
        if eligible_pids:
            chosen_pid = eligible_pids[0]
            assigned_pred.add(chosen_pid)
            assigned_gold.add(gid)
            matched_pairs.append({
                'pred_id': chosen_pid,
                'gold_id': gid,
                'match_type': 'PARTIAL_HIGH_SIMILARITY'
            })
            for dup_pid in eligible_pids[1:]:
                duplicate_gold_matches.append({'pred_id': dup_pid, 'gold_id': gid})

    unmatched_preds = [p for p in sorted_pids if p not in assigned_pred and p not in ambiguous_preds]
    unmatched_gold = [g for g in sorted(gold_info.keys()) if g not in assigned_gold]

    return {
        'matched_pairs': matched_pairs,
        'unmatched_predictions': unmatched_preds,
        'ambiguous_predictions': sorted(list(ambiguous_preds)),
        'duplicate_gold_matches': duplicate_gold_matches,
        'unmatched_gold': unmatched_gold
    }

def score_run(run_dir_path, gold_ref_path):
    run_meta = json.loads((run_dir_path / 'run_meta.json').read_text(encoding='utf-8'))
    pipeline_out = json.loads((run_dir_path / 'pipeline_output.json').read_text(encoding='utf-8'))
    gold_ref = json.loads(gold_ref_path.read_text(encoding='utf-8'))
    
    reqs = pipeline_out.get('requirements', [])
    tasks = pipeline_out.get('tasks', [])
    modules = pipeline_out.get('modules', [])
    relations = pipeline_out.get('relations', [])
    tests = pipeline_out.get('test_cases', [])
    trace = pipeline_out.get('traceability', {})
    trace_matrix = trace.get('matrix', []) if isinstance(trace, dict) else []
    
    mod_id_to_name = {m['id']: m['name'] for m in modules}
    req_to_pred_module = {}
    for t in tasks:
        rid = t.get('requirement_id')
        mid = t.get('module_id')
        if rid and mid in mod_id_to_name:
            req_to_pred_module[rid] = canonicalize(mod_id_to_name[mid])
            
    gold_details = gold_ref.get('requirement_details', {})
    if not gold_details:
        exp_assignments = gold_ref.get('expected_module_assignments', {})
        gold_details = {k: {'canonical': v, 'statement': k} for k, v in exp_assignments.items()}
        
    req_by_id = {r.get('id'): r for r in reqs}
    global_res = global_match_requirements(reqs, gold_details)
    
    matched_pairs = []
    for pair in global_res['matched_pairs']:
        pid = pair['pred_id']
        gid = pair['gold_id']
        r = req_by_id.get(pid, {})
        matched_pairs.append({
            'pred_id': pid,
            'gold_id': gid,
            'pred_module': req_to_pred_module.get(pid, 'UNASSIGNED'),
            'gold_module': canonicalize(gold_details[gid].get('canonical')),
            'summary': r.get('summary', ''),
            'match_type': pair.get('match_type', 'EXACT')
        })
        
    unmatched_predictions = global_res['unmatched_predictions']
    ambiguous_predictions = global_res['ambiguous_predictions']
    duplicate_gold_matches = global_res['duplicate_gold_matches']
    unmatched_gold_entries = global_res['unmatched_gold']
    
    tp = Counter()
    fp = Counter()
    fn = Counter()
    all_classes = set()
    correct = 0
    errors = []
    
    for pair in matched_pairs:
        p_mod = pair['pred_module']
        g_mod = pair['gold_module']
        all_classes.add(g_mod)
        all_classes.add(p_mod)
        
        if p_mod == g_mod:
            correct += 1
            tp[g_mod] += 1
        else:
            fp[p_mod] += 1
            fn[g_mod] += 1
            errors.append({
                'pred_id': pair['pred_id'],
                'gold_id': pair['gold_id'],
                'summary': pair['summary'],
                'expected': g_mod,
                'predicted': p_mod
            })
            
    total_matched = len(matched_pairs)
    accuracy = (correct / total_matched) if total_matched > 0 else 0.0
    
    # Penalized end-to-end accuracy: denominator is max(len(reqs), len(gold_details))
    penalized_denom = max(len(reqs), len(gold_details))
    penalized_accuracy = (correct / penalized_denom) if penalized_denom > 0 else 0.0
    
    class_metrics = {}
    precisions, recalls, f1s = [], [], []
    for cls in sorted(all_classes):
        if cls == 'UNASSIGNED':
            continue
        c_tp = tp[cls]
        c_fp = fp[cls]
        c_fn = fn[cls]
        
        c_prec = c_tp / (c_tp + c_fp) if (c_tp + c_fp) > 0 else 0.0
        c_rec = c_tp / (c_tp + c_fn) if (c_tp + c_fn) > 0 else 0.0
        c_f1 = (2 * c_prec * c_rec) / (c_prec + c_rec) if (c_prec + c_rec) > 0 else 0.0
        
        class_metrics[cls] = {
            'tp': c_tp, 'fp': c_fp, 'fn': c_fn,
            'precision': round(c_prec, 4),
            'recall': round(c_rec, 4),
            'f1': round(c_f1, 4)
        }
        precisions.append(c_prec)
        recalls.append(c_rec)
        f1s.append(c_f1)
        
    macro_precision = sum(precisions) / len(precisions) if precisions else 0.0
    macro_recall = sum(recalls) / len(recalls) if recalls else 0.0
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0
    
    req_ids = {r['id'] for r in reqs}
    task_req_ids = {t.get('requirement_id') for t in tasks if t.get('requirement_id')}
    uncovered_reqs = req_ids - task_req_ids
    test_req_ids = {t.get('requirement_id') for t in tests if t.get('requirement_id')}
    untested_reqs = req_ids - test_req_ids
    
    structural_integrity = {
        'total_requirements': len(reqs),
        'requirements_with_tasks': len(task_req_ids),
        'requirements_without_tasks': len(uncovered_reqs),
        'task_coverage_pct': round((len(task_req_ids) / len(reqs) * 100) if reqs else 0, 2),
        'total_modules': len(modules),
        'total_relations': len(relations),
        'total_tasks': len(tasks),
        'total_test_cases': len(tests),
        'untested_requirements_count': len(untested_reqs),
        'traceability_matrix_rows': len(trace_matrix)
    }
    
    report = {
        'run_id': run_meta['run_id'],
        'domain_key': run_meta['domain_key'],
        'project_title': run_meta['project_title'],
        'timestamp': run_meta['timestamp'],
        'llm_enabled': run_meta['llm_enabled'],
        'llm_extraction_succeeded': run_meta['llm_extraction_succeeded'],
        'fallback_used': run_meta['fallback_used'],
        'provider': run_meta['provider'],
        'model': run_meta['model'],
        'matching_summary': {
            'predicted_requirements_count': len(reqs),
            'reference_requirements_count': len(gold_details),
            'uniquely_matched_count': total_matched,
            'unmatched_predictions_count': len(unmatched_predictions),
            'ambiguous_predictions_count': len(ambiguous_predictions),
            'duplicate_gold_matches_count': len(duplicate_gold_matches),
            'unmatched_reference_count': len(unmatched_gold_entries)
        },
        'classification_evaluation': {
            'valid_matched_denominator': total_matched,
            'correct_classifications': correct,
            'accuracy': round(accuracy, 4),
            'penalized_end_to_end_accuracy': round(penalized_accuracy, 4),
            'macro_precision': round(macro_precision, 4),
            'macro_recall': round(macro_recall, 4),
            'macro_f1': round(macro_f1, 4),
            'per_class_metrics': class_metrics,
            'errors_sample': errors[:10],
            'total_errors': len(errors)
        },
        'structural_integrity': structural_integrity,
        'unsupported_metrics_declared': [
            'semantic_test_step_oracle: NOT EVALUATED (No independent ground-truth test assertions)',
            'code_level_traceability_oracle: NOT EVALUATED (No source code repository under analysis)',
            'dynamic_runtime_latency_oracle: NOT EVALUATED (Pipeline runs offline)'
        ]
    }
    return report
