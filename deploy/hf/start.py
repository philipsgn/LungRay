"""Download and verify the single serving checkpoint before starting uvicorn."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

FILENAME = "best_model_20_11.pth"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_checkpoint(root: Path = Path("/app")) -> Path:
    checkpoint = root / "checkpoints" / FILENAME
    config = json.loads((root / "configs/optimal_thresholds_20_11.json").read_text(encoding="utf-8"))
    expected = config["checkpoint_sha256"]
    if not checkpoint.is_file():
        repo = os.getenv("HF_MODEL_REPO")
        if not repo:
            raise RuntimeError("Checkpoint missing. Set HF_MODEL_REPO or provide checkpoints/best_model_20_11.pth.")
        from huggingface_hub import hf_hub_download
        checkpoint.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=checkpoint.parent) as staging:
            source = hf_hub_download(repo_id=repo, filename=FILENAME,
                revision=os.getenv("HF_MODEL_REVISION", "main"), token=os.getenv("HF_TOKEN"), local_dir=staging)
            candidate = Path(source)
            downloaded_hash = _sha256_file(candidate)
            if downloaded_hash != expected:
                raise RuntimeError("Downloaded checkpoint SHA-256 does not match the bundled threshold artifact.")
            os.replace(candidate, checkpoint)
    actual = _sha256_file(checkpoint)
    if actual != expected:
        raise RuntimeError("Checkpoint SHA-256 does not match the bundled threshold artifact.")
    return checkpoint


if __name__ == "__main__":
    ensure_checkpoint()
    os.environ["LUNGRAY_SERVING_PROFILE"] = "standard"
    os.environ["CHECKPOINT_PATH"] = "/app/checkpoints/" + FILENAME
    os.execvp("uvicorn", ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"])
