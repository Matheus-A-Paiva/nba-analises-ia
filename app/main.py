import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import create_tables
from app.routers import analysis, auth, games, health, matchups, players, teams

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


app = FastAPI(
    title="NBA Análises IA",
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.title = "NBA Análises IA API"
app.description = (
    "API protegida por JWT para consulta de dados da NBA e análise de confrontos. "
    "Use /auth/register ou /auth/login para obter um bearer token e envie-o no cabeçalho Authorization. "
    "O frontend deve buscar dados de confronto em chamadas separadas: GET /teams/{team_id}, "
    "GET /matchups/{team1_id}/{team2_id}/history, GET /matchups/{team1_id}/{team2_id}/top-scorers, "
    "GET /matchups/{team1_id}/{team2_id}/top-players e, quando necessário, GET /analysis/{team1_id}/{team2_id}."
)
app.version = "1.0.0"


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    security_schemes = openapi_schema.setdefault("components", {}).setdefault(
        "securitySchemes", {}
    )
    security_schemes.pop("HTTPBearer", None)
    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if isinstance(operation, dict) and operation.get("security"):
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(health.router)
app.include_router(games.router)
app.include_router(teams.router)
app.include_router(matchups.router)
app.include_router(players.router)
app.include_router(analysis.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
