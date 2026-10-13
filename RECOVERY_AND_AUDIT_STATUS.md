# ReqPilot AI — Recovery & Audit Status

Date: 2026-09-06

## Completed recovery fixes

- Reconciled `backend/app/models.py` with the live `backend/reqpilot.db` schema (23/23 tables; columns, nullability and SQLite type declarations matched).
- Restored the missing `TeamMember` ORM model.
- Restored `backend/app/api/auth.py` from recovered Python bytecode evidence.
- Removed the unsafe unknown-email login behavior that auto-created an admin account with a known password.
- Made normal application startup non-mutating by making schema creation and demo seeding explicit opt-in settings:
  - `INIT_DB_ON_STARTUP=false` by default
  - `SEED_DEMO_DATA_ON_STARTUP=false` by default
- Added JWT validation to `/api/auth/me`.
- Changed generated test-case status from `passed` to `not_run` because generation is not test execution.
- Removed the live Groq credential from the deliverable and added `.env.example` and backend `.gitignore`.

## Verification performed in this environment

- Python syntax compilation of modified backend files: PASS.
- SQLAlchemy model import/metadata construction using an isolated Base: PASS.
- Model/database schema comparison: PASS (23/23 tables; no column, nullability, or type drift).
- Existing backend agent unit tests: PASS (6/6).
- Deterministic end-to-end orchestrator execution on a controlled sample: PASS for execution; produced requirements, issues, clarifications, architecture, planning, tests, traceability and reports.
- Benchmark smoke tests exposed limitations: one duplicate case and one conflict case were not detected by the current deterministic detectors.
- Frontend production build could not be completed in this environment because frontend dependencies/types are not installed and network installation is unavailable.
- Live FastAPI HTTP testing could not be completed in this environment because the environment lacks the `aiosqlite` package required by the project's declared SQLite async driver.

## Known research/functional issues still requiring work

1. Deterministic extraction uses generic actor/action/object/outcome templates for many sentences; quality should be improved and evaluated against a real labelled dataset.
2. Deterministic duplicate/conflict detection misses cases in the included benchmark smoke suite.
3. Evaluation endpoint and frontend evaluation/ablation displays contain hardcoded research metrics; these must not be presented as measured experimental results until a real evaluation runner computes them.
4. Demo/reference seed content remains in `seed_data.py`; it is now opt-in at startup.
5. Real authenticated Groq inference has not been verified from this environment; provider errors currently fall back to deterministic processing and should be surfaced distinctly in production UX.
6. Frontend analysis progress contains simulated stage timing and should be connected to authoritative backend workflow state.

## Security note

The original deliverable contained a live Groq API credential. It was removed from this recovered deliverable. The previously exposed credential should be revoked/rotated before further use. Store the replacement only in a local `backend/.env` that is ignored by Git and never included in ZIPs.

## Next audit phase

Run the recovered project locally with its declared dependencies, verify live HTTP behavior against the existing database, then execute the original 20-point Phase 1 audit with real database persistence and restart checks. Do not claim research metrics until the evaluation suite is genuinely executed against labelled ground truth.
