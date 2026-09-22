from apps.api.app.api.routers.datasets import router as datasets_router
from apps.api.app.api.routers.runs import runs_router
from apps.api.app.api.routers.findings import findings_router
from apps.api.app.api.routers.investigations import investigations_router
from apps.api.app.api.routers.reports import reports_router

__all__ = [
    "datasets_router",
    "runs_router",
    "findings_router",
    "investigations_router",
    "reports_router",
]
