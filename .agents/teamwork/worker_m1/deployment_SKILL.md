# SKILL DUMP: deployment
# Source: c:\Users\TanPhat\Documents\AI_E\Chest X-rays\.agents\skills\deployment\SKILL.md

Quy trình đóng gói FastAPI backend, giao diện Next.js PACS Viewer và container hóa toàn bộ hệ thống bằng Docker Compose cho nền tảng LungRay.
- FastAPI endpoints: /health, /api/v1/predict, /api/v1/explain, /api/v1/audit
- Next.js UI: upload, multi-task dashboard, interactive heatmap with alpha slider, audit badge, OOD safety lockout banner
- Containerization: Dockerfile.backend (python:3.10-slim), Dockerfile.frontend (Next.js multi-stage), docker-compose.yml
