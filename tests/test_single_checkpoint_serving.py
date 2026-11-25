"""Exercise a real startup and real CAM with only the dated Standard checkpoint."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("profile", ["auto", "standard"])
def test_single_checkpoint_startup_predict_explain_and_cors(tmp_path, profile):
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "configs").mkdir()
    shutil.copy2(ROOT / "checkpoints/best_model_20_11.pth", tmp_path / "checkpoints")
    for name in ("optimal_thresholds_20_11.json", "ood_thresholds.json"):
        shutil.copy2(ROOT / "configs" / name, tmp_path / "configs")
    code = r'''
import asyncio, io, sys
import numpy as np
from PIL import Image
import httpx
# Same Windows sandbox event-loop workaround as the existing API suite.
if sys.platform == "win32":
    import asyncio.proactor_events
    class DummySocket:
        def setblocking(self, *args): pass
        def send(self, *args): return 0
        def recv(self, *args): return b""
        def close(self): pass
        def fileno(self): return -1
    def make_pipe(self):
        self._ssock = DummySocket(); self._csock = DummySocket(); self._internal_fds = 0
    asyncio.proactor_events.BaseProactorEventLoop._make_self_pipe = make_pipe
    asyncio.proactor_events.BaseProactorEventLoop._loop_self_reading = lambda self, *args: None
from app.backend.main import app, service
assert set(service.models) == {"standard"}
assert service.dense_unet is None
async def run():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/health")).status_code == 200
        models = (await client.get("/api/v1/models")).json()
        assert [model["id"] for model in models] == ["standard"]
        cors = await client.options("/api/v1/predict", headers={"Origin": "https://pacs-test.vercel.app", "Access-Control-Request-Method": "POST"})
        assert cors.status_code == 200 and cors.headers["access-control-allow-origin"] == "*"
        image = np.tile(np.linspace(0,255,512,dtype=np.uint8), (512,1))
        stream = io.BytesIO(); Image.fromarray(image).convert("RGB").save(stream, format="PNG")
        files = {"file": ("cxr.png", stream.getvalue(), "image/png")}
        prediction = await client.post("/api/v1/predict?tta_enabled=false", files=files)
        assert prediction.status_code == 200, prediction.text
        assert len(prediction.json()["head_a_prediction"]) == 14
        explanation = await client.post("/api/v1/explain", files=files, data={"model":"standard", "target_head":"head_a", "target_class":"2"})
        assert explanation.status_code == 200, explanation.text
        output = explanation.json()
        assert output["heatmap_rgba_base64"] and output["contour_rgba_base64"]
        assert output["mask_source"] in {"morphology", "morphology_fallback"}
        assert output["mask_warning"] and output["audit_pass"] is None
        missing = await client.post("/api/v1/predict?model=ag_mtcnet", files=files)
        assert missing.status_code == 422
asyncio.run(run())
print("SINGLE_CHECKPOINT_OK")
'''
    environment = dict(os.environ, PYTHONPATH=str(ROOT), LUNGRAY_SERVING_PROFILE=profile, CUDA_VISIBLE_DEVICES="", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2")
    environment.pop("CHECKPOINT_PATH", None)
    environment.pop("AG_MTCNET_CHECKPOINT", None)
    environment.pop("DENSE_UNET_CHECKPOINT", None)
    result = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, env=environment,
                            text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SINGLE_CHECKPOINT_OK" in result.stdout
