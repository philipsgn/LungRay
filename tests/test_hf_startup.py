"""HF startup provisions a verified single checkpoint without embedded credentials."""
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from deploy.hf.start import ensure_checkpoint, FILENAME


def prepare(root, contents=b"test-only-checkpoint"):
    (root / "configs").mkdir()
    (root / "configs/optimal_thresholds_20_11.json").write_text(json.dumps({"checkpoint_sha256": hashlib.sha256(contents).hexdigest()}))
    return contents


def test_hf_existing_checkpoint_verified_without_hub(tmp_path):
    data = prepare(tmp_path)
    (tmp_path / "checkpoints").mkdir()
    (tmp_path / "checkpoints" / FILENAME).write_bytes(data)
    assert ensure_checkpoint(tmp_path).read_bytes() == data
    (tmp_path / "checkpoints" / FILENAME).write_bytes(b"corrupt")
    with pytest.raises(RuntimeError, match="SHA-256"):
        ensure_checkpoint(tmp_path)


def test_hf_missing_checkpoint_requires_repository(tmp_path, monkeypatch):
    prepare(tmp_path)
    monkeypatch.delenv("HF_MODEL_REPO", raising=False)
    with pytest.raises(RuntimeError, match="HF_MODEL_REPO"):
        ensure_checkpoint(tmp_path)


def test_hf_download_verifies_before_installing(tmp_path, monkeypatch):
    data = prepare(tmp_path)
    monkeypatch.setenv("HF_MODEL_REPO", "owner/model")
    def download(**kwargs):
        assert kwargs["repo_id"] == "owner/model" and kwargs["filename"] == FILENAME
        path = Path(kwargs["local_dir"]) / FILENAME
        path.write_bytes(data)
        return str(path)
    monkeypatch.setitem(sys.modules, "huggingface_hub", SimpleNamespace(hf_hub_download=download))
    assert ensure_checkpoint(tmp_path).read_bytes() == data
    assert [path.name for path in (tmp_path / "checkpoints").iterdir()] == [FILENAME]
