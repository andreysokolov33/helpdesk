from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from starlette.responses import Response

from app.config import BASE_DIR

router = APIRouter()

_REACT_INDEX = BASE_DIR / "app" / "static" / "helpdesk" / "index.html"
_FAVICON = BASE_DIR / "app" / "static" / "images" / "Logo_dark.svg"


def _react_shell(title: str) -> HTMLResponse:
    """SPA-оболочка: ассеты собираются Vite в app/static/helpdesk/."""
    if not _REACT_INDEX.is_file():
        return HTMLResponse(
            content=(
                "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Helpdesk</title></head>"
                "<body style='font-family:system-ui;padding:2rem'>"
                "<p>Соберите фронтенд: <code>cd frontend && npm install && npm run build</code></p>"
                "</body></html>"
            ),
            status_code=503,
        )
    html = _REACT_INDEX.read_text(encoding="utf-8")
    html = re.sub(r"<title>[^<]*</title>", f"<title>{title}</title>", html, count=1)
    return HTMLResponse(content=html)


async def get_current_user(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user


@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request, _user: dict = Depends(get_current_user)):
    return _react_shell("Helpdesk — рабочий стол")


@router.get("/login", response_class=HTMLResponse)
async def login_page():
    return _react_shell("Helpdesk — вход")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    if _FAVICON.is_file():
        return FileResponse(_FAVICON, media_type="image/svg+xml")
    return Response(status_code=204)


@router.get("/{full_path:path}", response_class=HTMLResponse)
async def spa_catch_all(full_path: str, request: Request, _user: dict = Depends(get_current_user)):
    """Клиентские маршруты React (например /tickets, /stats) — та же оболочка SPA."""
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Not Found")
    if full_path in ("health", "ready", "docs", "redoc", "openapi.json", "favicon.ico"):
        raise HTTPException(status_code=404, detail="Not Found")
    return _react_shell("Helpdesk")
