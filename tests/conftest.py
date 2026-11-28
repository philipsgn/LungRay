"""
Shared PyTest fixtures for LungRay platform testing.
"""
import os
os.environ["NO_ALBUMENTATIONS_UPDATE"] = "1"
import pytest
import torch
import numpy as np


@pytest.fixture(autouse=True)
def windows_asyncio_test_wakeup(monkeypatch):
    """Support worker completion in the Windows sandbox's socket-free test loop.

    Existing API tests disable the Proactor self-pipe because localhost
    socketpair creation is unavailable here. A bounded IOCP poll is also needed
    to observe call_soon_threadsafe callbacks from real worker threads. This
    fixture affects tests only, never the deployed event loop.
    """
    import sys
    if sys.platform != "win32":
        return
    import asyncio.proactor_events
    import asyncio.windows_events

    class DummySocket:
        def setblocking(self, *args): pass
        def send(self, *args): return 0
        def recv(self, *args): return b""
        def close(self): pass
        def fileno(self): return -1

    def make_pipe(loop):
        loop._ssock = DummySocket()
        loop._csock = DummySocket()
        loop._internal_fds = 0

    original_select = asyncio.windows_events.IocpProactor.select

    def bounded_select(proactor, timeout=None):
        return original_select(proactor, 0.01 if timeout is None else min(timeout, 0.01))

    monkeypatch.setattr(asyncio.proactor_events.BaseProactorEventLoop, "_make_self_pipe", make_pipe)
    monkeypatch.setattr(asyncio.proactor_events.BaseProactorEventLoop, "_loop_self_reading", lambda *args: None)
    monkeypatch.setattr(asyncio.windows_events.IocpProactor, "select", bounded_select)


@pytest.fixture
def dummy_cxr_tensor():
    """Generates a dummy batch of CXR images (B=2, C=3, H=512, W=512)."""
    return torch.randn(2, 3, 512, 512)


@pytest.fixture
def dummy_nih_labels():
    """Generates multi-hot ground truth for NIH Head A (14 classes)."""
    return torch.randint(0, 2, (2, 14)).float()


@pytest.fixture
def dummy_tb_labels():
    """Generates binary ground truth for TB Head B."""
    return torch.randint(0, 2, (2, 1)).float()


@pytest.fixture
def dummy_covid_labels():
    """Generates binary ground truth for COVID Head C (COVIDx binary screening)."""
    return torch.randint(0, 2, (2, 1)).float()
