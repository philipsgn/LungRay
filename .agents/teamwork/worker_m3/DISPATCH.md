# Dispatch: Worker M3 — Master Verification & Quality Gate Runner

## Identity
- Role: Master Verification Worker
- Archetype: teamwork_worker
- Working Directory: c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m3\
- Parent: d86fe589-088e-415c-a8dd-43820b8e77d7

## Task
Execute the repository master verification runner:
`powershell -File scripts/verify.ps1`
(which executes `scripts/verify.py` using Python 3.10).

Verify:
1. Python syntax compilation (`compileall src tests`).
2. Linting checks.
3. Full repository test suite (`pytest tests -q --tb=short`). Confirm all 130+ unit/integration tests pass with 0 failures.
4. Check that no temporary files or test dumps remain in the repo (Rule 8: Lean Workspace).

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Input Files
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\ORIGINAL_REQUEST.md` (MANDATORY: read first)
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\PROJECT.md`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\scripts\verify.ps1`
- `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\scripts\verify.py`

## Output
Write full handoff report to `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m3\handoff.md` and send completion message to orchestrator.

## 2026-11-05T05:58:13Z
You are Worker M3. Read your dispatch instructions at `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m3\DISPATCH.md`.
MANDATORY: Read `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\ORIGINAL_REQUEST.md` before starting work.
Your working directory is `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m3\`.

MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Execute the repository master verification runner:
`powershell -File scripts/verify.ps1`
(which executes `scripts/verify.py` using Python 3.10).

Verify:
1. Python syntax check: `python -m compileall src tests -q`
2. Full pytest unit test suite: confirm all 130+ tests pass with 0 failures.
3. Clean workspace check: verify no temporary scratch files, orphan test dumps, or debug logs remain.

Write your full handoff report to `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m3\handoff.md` and notify orchestrator when done via send_message.
