"""ASGI composition and shared-model concurrency contracts (no Gradio SDK mock inference)."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.backend.gradio_mount import execute_model, mount_status_ui


# Match the existing Windows API suite's sandbox-safe event-loop self-pipe.
if sys.platform == "win32":
    import asyncio.proactor_events
    class _DummySocket:
        def setblocking(self, *args): pass
        def send(self, *args): return 0
        def recv(self, *args): return b""
        def close(self): pass
        def fileno(self): return -1
    def _make_pipe(self):
        self._ssock = _DummySocket()
        self._csock = _DummySocket()
        self._internal_fds = 0
    asyncio.proactor_events.BaseProactorEventLoop._make_self_pipe = _make_pipe
    asyncio.proactor_events.BaseProactorEventLoop._loop_self_reading = lambda self, *args: None


def test_api_priority_and_cors_survive_root_ui_mount():
    api = FastAPI()
    api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    paths = [("/health", "GET"), ("/api/v1/models", "GET"), ("/api/v1/predict", "POST"),
             ("/api/v1/explain", "POST"), ("/api/v1/rag-query", "POST")]
    async def handler(request: Request):
        return {"handler": "api", "path": request.url.path}
    for path, method in paths:
        api.add_api_route(path, handler, methods=[method])
    async def catch_all(request):
        return JSONResponse({"handler": "ui"})
    ui = Starlette(routes=[Route("/{path:path}", catch_all, methods=["GET", "POST"])])
    class GradioAdapter:
        @staticmethod
        def mount_gradio_app(parent, blocks, **kwargs):
            assert blocks == "status-ui" and kwargs == {"path": "/", "ssr_mode": False}
            parent.mount("/", ui)
            return parent
    combined = mount_status_ui(api, "status-ui", GradioAdapter)
    async def check():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=combined), base_url="http://test") as client:
            for path, method in paths:
                response = await client.request(method, path)
                assert response.status_code == 200 and response.json() == {"handler": "api", "path": path}
            assert (await client.get("/")).json()["handler"] == "ui"
            cors = await client.options("/api/v1/predict", headers={"Origin": "https://pacs.vercel.app", "Access-Control-Request-Method": "POST"})
            assert cors.status_code == 200 and cors.headers["access-control-allow-origin"] == "*"
    asyncio.run(check())


def test_shared_model_execution_does_not_overlap():
    state = {"active": 0, "peak": 0}
    def operation(value):
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        time.sleep(0.01)
        state["active"] -= 1
        return value
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda value: execute_model(operation, value), range(8)))
    assert results == list(range(8)) and state["peak"] == 1
