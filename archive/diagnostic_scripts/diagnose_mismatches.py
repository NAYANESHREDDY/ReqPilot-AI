import sys, os, re, json, asyncio
from pathlib import Path
sys.path.insert(0, os.path.abspath('backend'))
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('evaluation/multi_project/scripts'))

from backend.app.agents.task_agent import TaskDecompositionAgent
from backend.app.agents.extraction_agent import ExtractionAgent
from backend.app.agents.llm_adapter import LLMAdapter
from backend.app.agents.architecture_agent import ArchitectureAgent
from scorer import global_match_requirements, canonicalize

async def diagnose_domain(dkey, title):
    spec_path = Path(f'evaluation/multi_project/benchmark/{dkey}/specification.txt')
    text = spec_path.read_text(encoding='utf-8')
    chunks = [{'chunk_index': 0, 'section_title': 'Spec', 'page_number': 1, 'content': text, 'token_count': len(text.split())}]
    ext_agent = ExtractionAgent(LLMAdapter(api_key=''))
    arch_agent = ArchitectureAgent()
    task_agent = TaskDecompositionAgent()
    reqs = await ext_agent.extract_requirements(chunks, 'specification.txt')
    arch = arch_agent.generate_architecture(reqs, title)
    modules = arch['modules']
    task_res = await task_agent.decompose_requirements(reqs, modules)
    tasks = task_res['tasks']
    mod_id_to_name = {m['id']: m['name'] for m in modules}
    req_to_pred_module = {}
    for t in tasks:
        rid = t.get('requirement_id')
        mid = t.get('module_id')
        if rid and mid in mod_id_to_name:
            req_to_pred_module[rid] = canonicalize(mod_id_to_name[mid])
    gold_ref = json.loads(Path(f'evaluation/multi_project/benchmark/{dkey}/gold_reference.json').read_text(encoding='utf-8'))
    gold_details = gold_ref.get('requirement_details', {})
    global_res = global_match_requirements(reqs, gold_details)
    matched = global_res['matched_pairs']
    print(f'=== {dkey} MISMATCHES ===')
    for p in matched:
        pid = p['pred_id']
        gid = p['gold_id']
        pred_mod = req_to_pred_module.get(pid, 'UNASSIGNED')
        gold_mod = canonicalize(gold_details[gid].get('canonical'))
        if pred_mod != gold_mod:
            r = [req for req in reqs if req['id']==pid][0]
            raw_pred_mod = [mod_id_to_name[t['module_id']] for t in tasks if t.get('requirement_id')==pid and t.get('module_id') in mod_id_to_name]
            raw_pred_name = raw_pred_mod[0] if raw_pred_mod else 'NONE'
            print(f'{pid} -> {gid}: Gold=[{gold_mod}] vs Pred=[{pred_mod}] (RawModule={raw_pred_name})')
            print(f'   Text: {r.get("description", "")[:90]}')

async def main():
    for d, t in [('ecommerce_platform', 'E-Commerce Platform'), ('library_management', 'Library Management System'), ('banking_management', 'Core Banking Management System')]:
        await diagnose_domain(d, t)

asyncio.run(main())
