"""Hugging Face ZeroGPU Gradio Space Entrypoint for LungRay FastAPI Backend."""
from __future__ import annotations

import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("LUNGRAY_SERVING_PROFILE", "standard")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("NO_ALBUMENTATIONS_UPDATE", "1")

from deploy.hf.start import ensure_checkpoint

checkpoint_path = ensure_checkpoint(ROOT)
os.environ["CHECKPOINT_PATH"] = str(checkpoint_path)

import gradio as gr
from fastapi.middleware.cors import CORSMiddleware
from app.backend.main import app as fastapi_app

try:
    import spaces
except ImportError:
    class _DummySpaces:
        @staticmethod
        def GPU(fn=None, **_kwargs):
            return fn if fn is not None else (lambda f: f)
    spaces = _DummySpaces()


@spaces.GPU
def verify_zerogpu_runtime() -> str:
    """Satisfies Hugging Face ZeroGPU startup check."""
    return "LungRay API & ZeroGPU Runtime Ready"


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
    probe_btn = gr.Button("Verify ZeroGPU Runtime")
    probe_out = gr.Textbox(label="Runtime Status")
    probe_btn.click(fn=verify_zerogpu_runtime, outputs=probe_out)


if __name__ == "__main__":
    # Let Gradio + ZeroGPU supervisor manage port binding (avoids Errno 98 on 7860)
    status_ui.launch(server_name="0.0.0.0", prevent_thread_lock=True)

    # Inject all FastAPI endpoints ahead of Gradio's catch-all routes
    gradio_app = getattr(status_ui, "app", None) or getattr(getattr(status_ui, "server", None), "app", None)
    if gradio_app is not None:
        for route in reversed(fastapi_app.routes):
            gradio_app.router.routes.insert(0, route)
        gradio_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        gradio_app.middleware_stack = gradio_app.build_middleware_stack()

    status_ui.block_thread()
