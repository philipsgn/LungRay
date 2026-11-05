# Dispatch: Spec Miner Survey 3 (Verification & System Specifications)

## Timestamp: 2026-11-05T04:10:00Z

## Task Assignment
You are Spec Miner Survey 3. Your task is to investigate authoritative project specifications, quality gates, and verification scripts to establish the exact verification baseline and compliance checklist.

## Working Directory
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\spec_miner_survey_3\`

## Mandatory Inputs
You MUST read `ORIGINAL_REQUEST.md` before starting work:
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\ORIGINAL_REQUEST.md`

Also consult:
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\PLAN.md`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\PHASES.md`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\AGENTS.md`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\scripts\verify.ps1`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\tests\`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\pyproject.toml` / `requirements.txt`

## Scope of Investigation
1. **Verification Script (`scripts/verify.ps1`)**:
   - Inspect the exact commands, checks, and criteria inside `scripts/verify.ps1`.
   - Run or trace `scripts/verify.ps1` and `pytest tests/` to determine current passing status, any failing tests, test run duration, and environment prerequisites.
2. **Quality Gates & Acceptance Criteria**:
   - Trace Gates 1 through 6 in `PLAN.md` and `PHASES.md`.
   - Identify what has been marked completed vs pending in `PHASES.md` (e.g. 96.8% status).
   - What are the precise requirements for Gate 5 (Fullstack Deployment) and Gate 6 (Academic Reporting & Defense)?
3. **Integrity & Safety Checks**:
   - Check zero data leakage rules (Patient_ID splits).
   - Check fail-safe OOD lockout criteria (Free energy score threshold, behavior on non-CXR or corrupted images).
   - Check clean workspace rules (no temporary files, scratch scripts, debug dumps).
4. **Current Test Suite Inventory**:
   - Enumerate all test files in `tests/` and their respective focus areas (data pipeline, models, explainability, backend, integration).
   - Report pass/fail/skip counts.

## Deliverable
Write your comprehensive investigation findings to:
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\spec_miner_survey_3\handoff.md`

Include:
- Verification baseline (current output/status of tests)
- Specification matrix for Gates 5 & 6
- Gaps between current codebase and acceptance criteria
- Concrete test verification checklist


## 2026-11-05T04:23:06Z
[Message from d86fe589-088e-415c-a8dd-43820b8e77d7]
You are Spec Miner Survey 3. Read your dispatch instructions at `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\spec_miner_survey_3\DISPATCH.md`.
MANDATORY: Read `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\ORIGINAL_REQUEST.md` before starting work.
Your working directory is `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\spec_miner_survey_3\`.
Probe authoritative sources (PLAN.md, PHASES.md, AGENTS.md, `scripts/verify.ps1`, `tests/`) to map exact specifications, quality gates, test execution baseline, and zero data leakage / clean workspace constraints.
Write your complete handoff report to `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\spec_miner_survey_3\handoff.md` and notify the orchestrator when finished.
