from datetime import date

from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_current_user
from app.schemas.api import ErrorResponse, GameResponse
from app.services import cache_service, nba_service

router = APIRouter(tags=["games"])

GAMES_CACHE_HEADERS = {
    "Cache-Control": {
        "description": "Browser cache policy for the response.",
        "schema": {"type": "string", "example": "public, max-age=600"},
    },
    "X-Cache": {
        "description": "Cache status for the response. Values are miss, hit, or stale.",
        "schema": {"type": "string", "example": "hit"},
    },
}


@router.get(
    "/games",
    response_model=list[GameResponse],
    summary="List games for a specific date",
    description="Returns NBA games for one date. Frontends should call this route once per date they need, for example three separate calls for today, tomorrow, and the next day.",
    responses={
        200: {"description": "Games for the requested date.", "headers": GAMES_CACHE_HEADERS},
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        503: {"model": ErrorResponse, "description": "NBA games service timed out."},
    },
    operation_id="getGamesByDate",
)
def get_games(
    response: Response,
    game_date: date = Query(
        ..., alias="date", description="Game date in YYYY-MM-DD format.", example="2026-04-15"
    ),
    _=Depends(get_current_user),
):
    games, cache_status = nba_service.get_games_by_date(game_date, with_cache_status=True)
    cache_service.apply_cache_headers(
        response, cache_status, nba_service.GAMES_BY_DATE_CACHE_TTL
    )
    return games
