"""Hugging Face Gradio Space Entrypoint for LungRay FastAPI Backend (Free Tier)."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LUNGRAY_SERVING_PROFILE", "standard")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from deploy.hf.start import FILENAME, ensure_checkpoint

checkpoint_path = ensure_checkpoint(ROOT)
os.environ["CHECKPOINT_PATH"] = str(checkpoint_path)

import gradio as gr
import uvicorn
from app.backend.main import app as fastapi_app

with gr.Blocks(title="LungRay Standard API") as status_ui:
    gr.Markdown(
        "# LungRay Enterprise Clinical API\n"
        "**Status:** Online (Single-Checkpoint Standard CADx `best_model_20_11.pth`)\n\n"
        "### Active Endpoints for Vercel PACS Frontend\n"
        "- `GET /health`\n"
        "- `GET /api/v1/models`\n"
        "- `POST /api/v1/predict`\n"
        "- `POST /api/v1/explain`\n"
        "- `POST /api/v1/rag-query`\n"
    )

app = gr.mount_gradio_app(fastapi_app, status_ui, path="/")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
