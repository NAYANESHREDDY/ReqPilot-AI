import json
import csv
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').resolve()))
from evaluation.multi_project.scripts.scorer import global_match_requirements, canonicalize

run_dir = Path('evaluation/multi_project/runs/hospital_management_remediation_20261013_225655_2c7aed3e')
gold_path = Path('evaluation/multi_project/benchmark/hospital_management/gold_reference.json')
cur_path = Path('evaluation/multi_project/benchmark/hospital_management/gold_reference_curated_v2.1.json')

pipe_out = json.loads((run_dir / 'pipeline_output.json').read_text(encoding='utf-8'))
orig_ref = json.loads(gold_path.read_text(encoding='utf-8'))
cur_ref = json.loads(cur_path.read_text(encoding='utf-8'))

reqs = pipe_out.get('requirements', [])
tasks = pipe_out.get('tasks', [])
modules = pipe_out.get('modules', [])

mod_id_to_name = {m['id']: m['name'] for m in modules}
req_to_pred_module = {}
for t in tasks:
    rid = t.get('requirement_id')
    mid = t.get('module_id')
    if rid and mid in mod_id_to_name:
        req_to_pred_module[rid] = canonicalize(mod_id_to_name[mid])

orig_details = orig_ref.get('requirement_details', {})
cur_details = cur_ref.get('requirement_details', {})
orig_asg = orig_ref.get('expected_module_assignments', {})
cur_asg = cur_ref.get('expected_module_assignments', {})

match_res = global_match_requirements(reqs, orig_details)
matched_pairs = match_res['matched_pairs']

clear_benchmark_errors = {
    'FR-013', 'FR-023', 'FR-026', 'FR-027', 'FR-028', 'FR-049', 'FR-068',
    'FR-074', 'FR-076', 'FR-086', 'FR-090', 'FR-099', 'FR-102', 'FR-106',
    'NFR-001', 'NFR-002', 'NFR-003', 'NFR-006'
}

ambiguous_ids = {
    'FR-016', 'FR-054', 'FR-058', 'FR-064', 'FR-087', 'FR-101', 'FR-103',
    'FR-108', 'FR-109', 'FR-110', 'FR-111', 'FR-112', 'NFR-011', 'NFR-012'
}

audit_rows = []

for p in matched_pairs:
    pid = p['pred_id']
    gid = p['gold_id']
    st = orig_details[gid]['statement']
    o_lbl = orig_asg.get(gid)
    c_lbl = cur_asg.get(gid)
    p_lbl = req_to_pred_module.get(pid, 'UNASSIGNED')
    o_canon = canonicalize(o_lbl)
    c_canon = canonicalize(c_lbl)
    
    st_l = st.lower()
    
    # 1. UNASSIGNED_OR_NULL
    if o_lbl == 'UNASSIGNED_OR_NULL':
        discrepancy_category = 'BENCHMARK_UNASSIGNED_LABEL'
        evidence = f"Original gold explicitly marks {gid} as UNASSIGNED_OR_NULL. Scorer treats this as expected class UNASSIGNED_OR_NULL (or UNASSIGNED), making it impossible for any valid architectural service prediction to match."
        review_status = 'REQUIRES_HUMAN_REVIEW'
        
        if any(w in st_l for w in ['prescription', 'dispens', 'medicine', 'drug']):
            rationale = f"Requirement concerns prescription/pharmacy clinical workflow. Curated assigns [{c_lbl}]. Can map to Application Data Store (generic enterprise persistence) or a dedicated Pharmacy/Dispensing module."
        elif any(w in st_l for w in ['laboratory', 'lab test', 'lab result']):
            rationale = f"Requirement concerns laboratory diagnostics workflow. Curated assigns [{c_lbl}]. Can map to Application Data Store, Booking (test scheduling), or a dedicated Laboratory module."
        elif any(w in st_l for w in ['bed', 'ward', 'occupied']):
            rationale = f"Requirement concerns inpatient bed/ward assignment. Curated assigns [{c_lbl}]. Can map to Booking & Scheduling (space reservation), Data Store, or a dedicated Inpatient unit."
        elif any(w in st_l for w in ['bill', 'hospital charge']):
            rationale = f"Requirement concerns billing calculation or bill viewing. Curated assigns [{c_lbl}]. Functional capability is Payment Management."
        elif any(w in st_l for w in ['role', 'user account']):
            rationale = f"Requirement concerns RBAC role assignment or account lifecycle. Curated assigns [{c_lbl}]. Functional capability is Authentication & Authorization."
        elif any(w in st_l for w in ['backup', 'recovery']):
            rationale = f"Requirement concerns database backup/disaster recovery. Curated assigns [{c_lbl}]. Functional capability is Application Data Store."
        elif any(w in st_l for w in ['search']):
            rationale = f"Requirement concerns search latency/performance for patients and doctors. Curated assigns [{c_lbl}]. Functional capability is Search & Discovery."
        else:
            rationale = f"Unassigned gold requirement. Curated assigns [{c_lbl}]. Requires human review."
            
    # 2. CLEAR BENCHMARK ERROR IN ORIGINAL GOLD
    elif gid in clear_benchmark_errors:
        discrepancy_category = 'CLEAR_BENCHMARK_ERROR'
        review_status = 'REQUIRES_HUMAN_REVIEW'
        if gid == 'FR-013':
            evidence = 'Original gold assigns Payment Management to: "Patients should receive notifications about appointments, laboratory results, payments, and other relevant events."'
            rationale = 'Notification dispatch across multiple system events is fundamentally a Notification Service responsibility, not Payment Management.'
        elif gid in ['FR-023', 'FR-026', 'FR-027', 'FR-028']:
            evidence = f'Original gold assigns Authentication & Authorization to reception/inpatient operational requirement: "{st[:75]}"'
            rationale = 'Patient registration, demographic updates, inpatient admission, and transfers are patient master data / clinical admission workflows, not user credential/token authentication.'
        elif gid == 'FR-049':
            evidence = 'Original gold assigns Authentication & Authorization to: "Authorized staff should be able to assign an available bed to an admitted patient."'
            rationale = 'Bed assignment is an inpatient bed management / scheduling hold function, not an authentication/security capability.'
        elif gid == 'FR-068':
            evidence = 'Original gold assigns Booking & Scheduling to: "The system should send appointment reminders before scheduled consultations."'
            rationale = 'Automated reminder delivery is a communication/alerting function belonging to Notification Service.'
        elif gid == 'FR-074':
            evidence = 'Original gold assigns Payment Management to: "Updates to appointment, bed, laboratory, and billing status should be reflected without requiring unnecessary manual refreshes."'
            rationale = 'Cross-cutting real-time status synchronization spans multiple domains; erroneously categorized under Payment Management in gold.'
        elif gid == 'FR-076':
            evidence = 'Original gold assigns Payment Management to: "Billing and payment information should not be lost after a temporary system restart."'
            rationale = 'Data durability/persistence across restarts is an Application Data Store requirement, though billing domain is mentioned.'
        elif gid == 'FR-086':
            evidence = 'Original gold assigns Payment Management to: "Completed appointments, consultation records, prescriptions, laboratory results, bills, and payment records should be maintained in accordance with medical-record retention requirements."'
            rationale = 'Comprehensive clinical and administrative medical record retention is an Application Data Store responsibility; gold mislabeled under Payment because "bills, and payment records" was in the middle of the text.'
        elif gid == 'FR-090':
            evidence = 'Original gold assigns Payment Management to: "Administrative Requirements Administrators should be able to manage patients, doctors, nurses, receptionists, pharmacists, and laboratory staff accounts."'
            rationale = 'Staff user account and identity administration is an Authentication & Authorization responsibility; Payment Management assignment in gold is an evident section-parsing defect.'
        elif gid == 'FR-099':
            evidence = 'Original gold assigns Reporting & Analytics to: "A patient payment must not be marked as successful when the payment provider reports a failure."'
            rationale = 'Payment gateway transaction integrity and success/failure reconciliation belongs to Payment Management, not Reporting.'
        elif gid == 'FR-102':
            evidence = 'Original gold assigns Booking & Scheduling to: "Reporting and Auditability Every appointment creation, cancellation, and rescheduling operation should be recorded in an operational audit log."'
            rationale = 'Audit trail preservation is an Application Data Store or Reporting & Auditability capability; Booking & Scheduling assignment conflates the business event with the audit storage capability.'
        elif gid == 'FR-106':
            evidence = 'Original gold assigns Reporting & Analytics to: "Payment state transitions should have a traceable record."'
            rationale = 'Audit record logging for payment transitions belongs to Application Data Store (or Payment ledger), not analytical reporting.'
        elif gid in ['NFR-001', 'NFR-002', 'NFR-003']:
            evidence = f'Original gold assigns API Gateway to functional availability query: "{st[:75]}"'
            rationale = 'Doctor schedule availability and bed availability lookups are core Booking & Scheduling (or Inpatient) functional queries, not API gateway reverse proxying.'
        elif gid == 'NFR-006':
            evidence = 'Original gold assigns API Gateway to: "Performance The system should remain responsive when a large number of patients and hospital staff search for doctors, view schedules, or perform operational tasks simultaneously."'
            rationale = 'System search and schedule responsiveness under load is an architectural performance constraint; curated routes to Search & Discovery.'
            
    # 3. AMBIGUOUS / MULTI-CAPABILITY REQUIREMENTS
    elif gid in ambiguous_ids:
        discrepancy_category = 'AMBIGUOUS_MULTI_CAPABILITY'
        review_status = 'REQUIRES_HUMAN_REVIEW'
        evidence = f'Requirement text combines distinct capability concepts: "{st[:80]}"'
        if 'audit' in st_l or 'traceable' in st_l:
            rationale = 'Overlaps Application Data Store (audit log persistence) with Reporting & Analytics (auditability reporting and operational traceability).'
        elif 'access' in st_l or 'confidential' in st_l or 'unauthorized' in st_l:
            rationale = 'Overlaps Authentication & Authorization (data access restriction / permission policy) with Application Data Store (confidential medical records domain entity).'
        elif 'specified whether' in st_l:
            rationale = 'Explicitly documented in specification as an "Ambiguous Stakeholder Point"; capability assignment depends on unfinalized business policy.'
        else:
            rationale = 'Contains overlapping functional concerns across multiple architectural services.'
            
    # 4. MODEL MISCLASSIFICATION (Model is genuinely wrong)
    elif p_lbl != o_canon and o_canon != 'UNASSIGNED_OR_NULL':
        discrepancy_category = 'GENUINE_MODEL_MISTAKE'
        review_status = 'MODEL_ERROR_CONFIRMED'
        evidence = f'Original gold assigns [{o_lbl}] ({o_canon}), which aligns directly with the requirement text: "{st[:75]}". Model predicted [{p_lbl}].'
        rationale = f'Model incorrectly routed the requirement to {p_lbl} instead of the legitimate functional owner {o_canon}.'
        
    # 5. CLEARLY CORRECT
    else:
        discrepancy_category = 'LABEL_MATCH_CORRECT'
        review_status = 'VERIFIED_CORRECT'
        evidence = f'Requirement "{st[:75]}" correctly aligns with assigned gold module [{o_lbl}].'
        rationale = f'Gold label {o_lbl} is an accurate and unambiguous mapping for this functional requirement.'
        
    audit_rows.append({
        'requirement_id': gid,
        'prediction_id': pid,
        'requirement_text': st,
        'original_gold_label': o_lbl,
        'model_predicted_module': p_lbl,
        'curated_gold_label': c_lbl,
        'discrepancy_category': discrepancy_category,
        'evidence': evidence,
        'rationale': rationale,
        'review_status': review_status
    })

# Save JSON audit report
out_json_path = Path('evaluation/multi_project/benchmark/hospital_management/hospital_ground_truth_audit.json')
out_json_path.write_text(json.dumps(audit_rows, indent=2, ensure_ascii=False), encoding='utf-8')
print('Wrote JSON audit report to:', out_json_path)

# Save CSV audit report
out_csv_path = Path('evaluation/multi_project/benchmark/hospital_management/hospital_ground_truth_audit.csv')
fieldnames = [
    'requirement_id', 'prediction_id', 'requirement_text', 'original_gold_label',
    'model_predicted_module', 'curated_gold_label', 'discrepancy_category',
    'evidence', 'rationale', 'review_status'
]
with open(out_csv_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(audit_rows)
print('Wrote CSV audit report to:', out_csv_path)

cat_counts = {}
st_counts = {}
for r in audit_rows:
    c = r['discrepancy_category']
    s = r['review_status']
    cat_counts[c] = cat_counts.get(c, 0) + 1
    st_counts[s] = st_counts.get(s, 0) + 1

print('\nDiscrepancy Category counts:')
for k, v in cat_counts.items():
    print(f'  {k}: {v}')

print('\nReview Status counts:')
for k, v in st_counts.items():
    print(f'  {k}: {v}')
