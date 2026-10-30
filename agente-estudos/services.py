# ruff: noqa
"""Registra as rotas do front-end customizado (verde e preto) no servidor ADK."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from google.adk.cli.dev_server import DevServer

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_HTML = BASE_DIR / "frontend" / "index.html"
CSV_FILE = BASE_DIR / "planos" / "plano-de-estudos.csv"


def attach_frontend_routes(app: FastAPI) -> FastAPI:
    """Adiciona o front-end verde e preto em `/` e `/ui` e endpoints do CSV."""
    if getattr(app.state, "custom_frontend_attached", False):
        return app

    # Remove o redirecionamento padrão de "/" para "/dev-ui/", mantendo "/dev-ui/" ativo
    app.router.routes = [
        route
        for route in app.router.routes
        if getattr(route, "path", None) != "/"
    ]

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    @app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
    async def serve_custom_frontend() -> HTMLResponse:
        if not FRONTEND_HTML.is_file():
            raise HTTPException(status_code=404, detail="Front-end não encontrado.")
        return HTMLResponse(
            content=FRONTEND_HTML.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/api/planos/csv", response_class=JSONResponse)
    async def get_plano_csv() -> JSONResponse:
        if not CSV_FILE.is_file():
            return JSONResponse({"exists": False, "content": ""})
        return JSONResponse(
            {
                "exists": True,
                "content": CSV_FILE.read_text(encoding="utf-8"),
            },
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/api/planos/csv/download")
    async def download_plano_csv() -> FileResponse:
        if not CSV_FILE.is_file():
            raise HTTPException(
                status_code=404,
                detail="Arquivo plano-de-estudos.csv ainda não foi gerado.",
            )
        return FileResponse(
            path=CSV_FILE,
            media_type="text/csv; charset=utf-8",
            filename="plano-de-estudos.csv",
            headers={"Cache-Control": "no-store"},
        )

    app.state.custom_frontend_attached = True
    return app


if not getattr(DevServer.get_fast_api_app, "_custom_frontend_patched", False):
    _original_get_fast_api_app = DevServer.get_fast_api_app

    def _patched_get_fast_api_app(self: DevServer, **kwargs: Any) -> FastAPI:
        app = _original_get_fast_api_app(self, **kwargs)
        return attach_frontend_routes(app)

    _patched_get_fast_api_app._custom_frontend_patched = True  # type: ignore[attr-defined]
    DevServer.get_fast_api_app = _patched_get_fast_api_app  # type: ignore[method-assign]
