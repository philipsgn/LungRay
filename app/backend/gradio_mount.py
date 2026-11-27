"""Compose the API before Gradio root routes; retain the API middleware stack."""
from threading import RLock

_execution_lock = RLock()


def execute_model(function, *args, **kwargs):
    """Prevent shared Grad-CAM hooks/eval state from overlapping in worker threads."""
    with _execution_lock:
        return function(*args, **kwargs)


def mount_status_ui(api_app, status_ui, gradio):
    # Parent API routes are already registered. Root mount is deliberately last.
    return gradio.mount_gradio_app(api_app, status_ui, path="/", ssr_mode=False)
