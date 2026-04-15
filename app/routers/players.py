from fastapi import APIRouter, Depends, Query, Response

from app.dependencies import get_current_user
from app.schemas.api import ErrorResponse, TopScorersResponse
from app.services import cache_service, nba_service

router = APIRouter(tags=["players"])

PLAYER_CACHE_HEADERS = {
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
    "/players/top-scorers",
    response_model=TopScorersResponse,
    summary="List top scorers across the league",
    description="Returns the league scoring leaders ordered by points per game. The result is cached because the underlying NBA stats endpoint is expensive.",
    responses={
        200: {"description": "League scoring leaders.", "headers": PLAYER_CACHE_HEADERS},
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        503: {"model": ErrorResponse, "description": "NBA player stats service timed out."},
    },
    operation_id="getLeagueTopScorers",
)
def get_players_top_scorers(
    response: Response,
    limit: int = Query(15, ge=1, le=50, description="Maximum number of players to return."),
    _=Depends(get_current_user),
):
    safe_limit = max(1, min(limit, 50))
    top_scorers, cache_status = nba_service.get_top_scorers_global(
        safe_limit, with_cache_status=True
    )
    cache_service.apply_cache_headers(
        response, cache_status, nba_service.TOP_SCORERS_CACHE_TTL
    )
    return {"top_scorers": top_scorers}
