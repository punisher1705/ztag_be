"""
Health check endpoints.

/healthz — liveness: is the process running at all?
/readyz  — readiness: can it actually reach its dependencies (DB, Redis)?

Kept separate on purpose: Kubernetes uses these differently — a failed
liveness probe restarts the pod, a failed readiness probe just pulls it
out of the load-balancer rotation without restarting it.
"""
from apiflask import APIBlueprint

from app.core.config import get_settings
from app.core.version import __version__

health_bp = APIBlueprint("health", __name__)


@health_bp.get("/healthz")
def liveness():
    """Basic liveness check — process is up and config loaded."""
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "env": settings.app_env,
    }


@health_bp.get("/readyz")
def readiness():
    """
    Readiness check — will be extended to actually ping MySQL/Redis
    once app/db/session.py and the redis client are wired in.
    For now it mirrors liveness as a placeholder.
    """
    return {"status": "ready"}