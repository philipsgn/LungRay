"""Hugging Face ZeroGPU Gradio Space Entrypoint for LungRay FastAPI Backend."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = next((path for path in (Path(__file__).resolve().parent, *Path(__file__).resolve().parents)
             if (path / "src").is_dir()), Path(__file__).resolve().parent)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LUNGRAY_SERVING_PROFILE", "standard")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from deploy.hf.start import ensure_checkpoint

os.chdir(ROOT)  # Threshold and OOD configs must resolve beside the verified checkpoint.
checkpoint_path = ensure_checkpoint(ROOT)
os.environ["CHECKPOINT_PATH"] = str(checkpoint_path)

import gradio as gr

try:
    import spaces
except ImportError:
    class _DummySpaces:
        @staticmethod
        def GPU(fn=None, **_kwargs):
            return fn if fn is not None else (lambda f: f)
    spaces = _DummySpaces()


from app.backend.main import app as fastapi_app
from app.backend.gradio_mount import mount_status_ui


@spaces.GPU
def verify_zerogpu_runtime() -> str:
    """Probe device availability only; REST inference is explicitly CPU-only."""
    import torch
    if not torch.cuda.is_available():
        return "CPU runtime active. No GPU execution has been verified; REST inference remains CPU."
    return f"Probe sees {torch.cuda.get_device_name(0)}. REST inference remains CPU."


with gr.Blocks(title="LungRay Standard API") as status_ui:
    gr.Markdown(
        "# LungRay Enterprise Clinical API\n"
        "**Status:** CPU REST API (Single-Checkpoint Standard CADx `best_model_20_11.pth`)\n\n"
        "### Active Endpoints for Vercel PACS Frontend\n"
        "- `GET /health`\n"
        "- `GET /api/v1/models`\n"
        "- `POST /api/v1/predict`\n"
        "- `POST /api/v1/explain`\n"
        "- `POST /api/v1/rag-query`\n"
    )
    probe_btn = gr.Button("Probe device availability")
    probe_out = gr.Textbox(label="Runtime Status")
    probe_btn.click(fn=verify_zerogpu_runtime, outputs=probe_out)


# Compose before accepting traffic; direct route injection after launch loses CORS.
application = mount_status_ui(fastapi_app, status_ui, gr)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(application, host="0.0.0.0", port=7860, workers=1)
