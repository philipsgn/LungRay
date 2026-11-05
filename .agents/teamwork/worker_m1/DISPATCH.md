# Dispatch: Worker M1 (Fullstack PACS Production & Docker Stack)

## Timestamp: 2026-11-05T05:20:00Z

## Task Assignment
You are Worker M1. Your objective is to finalize the Fullstack PACS Web Application & Docker deployment stack for production readiness.

## Working Directory
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m1\`

## Mandatory Inputs
You MUST read `ORIGINAL_REQUEST.md` before starting work:
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\ORIGINAL_REQUEST.md`
Also consult `c:\Users\TanPhat\Documents\AI_E\Chest X-rays\PROJECT.md`.

## Mandatory Integrity Warning
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Detailed Scope of Work
1. **Containerization Artifacts**:
   - Create production-ready `Dockerfile.backend`:
     - Base image `python:3.10-slim`.
     - Install requirements from `requirements.txt`.
     - Copy `src/`, `app/backend/`, `checkpoints/`, `configs/`.
     - CMD: `uvicorn app.backend.main:app --host 0.0.0.0 --port 8000`.
   - Create production-ready `Dockerfile.frontend`:
     - Multi-stage build for Next.js 14 (base, deps, builder, runner).
     - Working directory `/app`, expose port 3000.
     - Build Next.js app and start with standalone or next start.
   - Create `docker-compose.yml`:
     - Service `backend`: build `Dockerfile.backend`, ports `"8000:8000"`, volume mounts/checkpoints, environment variables (`PORT=8000`, `PYTHONUNBUFFERED=1`).
     - Service `frontend`: build `Dockerfile.frontend`, ports `"3000:3000"`, environment variable `NEXT_PUBLIC_API_BASE=http://localhost:8000`, depends_on `backend`.
2. **PACS Web Integration & Verification**:
   - Verify `app/backend/main.py`, `app/backend/schemas.py`, and `app/backend/services.py` are properly handling all routes (`/health`, `/api/v1/predict`, `/api/v1/explain`, `/api/v1/audit`).
   - Verify Fail-Safe OOD Lockout handling: ensure `SafetyPolicy` evaluation properly triggers when energy is out of bounds or entropy is high, and ensures `report` is blocked and frontend shows warning banner and lockout watermarked heatmap.
   - Verify Alpha slider blending: confirm frontend `AlphaSlider.tsx` adjusts heatmap opacity from 0% to 100% (default 45%) with `mixBlendMode: "screen"`.
3. **Execution & Self-Testing**:
   - Run unit tests for backend and OOD safety:
     `pytest tests/test_api_backend.py tests/test_ood_safety.py -v`
   - Document all test outcomes and commands in your handoff report.
   - Clean up any temporary scratch files or test artifacts.

## Deliverable
Write your complete handoff report to:
`c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\teamwork\worker_m1\handoff.md`
Notify the orchestrator via `send_message` when complete.

## 2026-11-05T05:36:44Z
**Context**: M1 Fullstack PACS Testing and Docker Stack
**Content**: Root cause of the hang in `tests/test_api_backend.py`:
In `tests/test_api_backend.py`, Starlette's `TestClient(app)` hangs on Windows Python 3.10 due to `anyio>=4.0` `start_blocking_portal()` subthread deadlock.
Fix: In `tests/test_api_backend.py`, replace the `client` fixture with native `httpx.ASGITransport`:
```python
import httpx

@pytest.fixture(scope="module")
def client():
    transport = httpx.ASGITransport(app=app)
    with httpx.Client(transport=transport, base_url="http://testserver") as c:
        yield c
```
Also ensure `Dockerfile.frontend` and `docker-compose.yml` are written, run `pytest tests/test_api_backend.py tests/test_ood_safety.py -v`, write your handoff report to `handoff.md`, and notify orchestrator when done.
**Action**: Implement the ASGITransport fixture fix, complete Dockerfile.frontend & docker-compose.yml, run tests, and write handoff.md.
