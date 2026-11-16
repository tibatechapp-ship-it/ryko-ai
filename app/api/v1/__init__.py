"""إصدار v1 من واجهة API."""

from app.api.v1.routes.agents import router as agents_router  # noqa: F401
from app.api.v1.routes.chat import router as chat_router  # noqa: F401
