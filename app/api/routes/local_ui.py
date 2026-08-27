"""Fixed local UI routes with runtime-scoped CSRF delivery."""

from collections.abc import Callable
from html import escape
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, Response

_ASSET_ROOT = Path(__file__).resolve().parent.parent / "static" / "local_ui"
_CSRF_PLACEHOLDER = "__LUXIOM_CSRF_TOKEN__"
_CONTENT_SECURITY_POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; "
    "img-src 'self'; connect-src 'self'; font-src 'none'; "
    "object-src 'none'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none';"
)


def _read_asset(filename: str) -> str:
    return (_ASSET_ROOT / filename).read_text(encoding="utf-8")


def create_local_ui_router(
    csrf_token_supplier: Callable[[], str],
) -> APIRouter:
    """Create three fixed UI routes bound to one runtime token supplier."""

    router = APIRouter(prefix="/local/ui", tags=["Local UI"])

    @router.get("", include_in_schema=False)
    async def local_ui() -> HTMLResponse:
        template = _read_asset("index.html")
        if template.count(_CSRF_PLACEHOLDER) != 1:
            raise RuntimeError("The local UI template is invalid.")
        token = csrf_token_supplier()
        if not isinstance(token, str) or not token:
            raise RuntimeError("The local UI is unavailable.")
        document = template.replace(
            _CSRF_PLACEHOLDER,
            escape(token, quote=True),
        )
        return HTMLResponse(
            document,
            headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": _CONTENT_SECURITY_POLICY,
                "Referrer-Policy": "no-referrer",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @router.get("/styles.css", include_in_schema=False)
    async def local_ui_styles() -> Response:
        return Response(
            _read_asset("styles.css"),
            media_type="text/css",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    @router.get("/app.js", include_in_schema=False)
    async def local_ui_script() -> Response:
        return Response(
            _read_asset("app.js"),
            media_type="application/javascript",
            headers={"X-Content-Type-Options": "nosniff"},
        )

    return router
