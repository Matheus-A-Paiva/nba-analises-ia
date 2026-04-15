from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response

from app.dependencies import get_current_user
from app.schemas.api import (
    ErrorResponse,
    HeadToHeadGame,
    TopPlayersByMetricResponse,
    TopScorersResponse,
)
from app.services import cache_service, nba_service

router = APIRouter(prefix="/matchups", tags=["matchups"])

MATCHUP_CACHE_HEADERS = {
    "Cache-Control": {
        "description": "Browser cache policy for the response.",
        "schema": {"type": "string", "example": "public, max-age=600"},
    },
    "X-Cache": {
        "description": "Cache status for the response. Values are miss, hit, or stale.",
        "schema": {"type": "string", "example": "hit"},
    },
}


def _validate_matchup(team1_id: int, team2_id: int) -> None:
    if nba_service.get_team_info(team1_id) is None or nba_service.get_team_info(team2_id) is None:
        raise HTTPException(status_code=404, detail="One or both teams were not found")


@router.get(
    "/{team1_id}/{team2_id}/history",
    response_model=list[HeadToHeadGame],
    summary="List recent head-to-head games",
    description="Returns the most recent direct meetings between two teams. Frontends can call this independently from the team summary and leader endpoints.",
    responses={
        200: {"description": "Recent head-to-head games.", "headers": MATCHUP_CACHE_HEADERS},
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        404: {"model": ErrorResponse, "description": "One or both teams were not found."},
        503: {"model": ErrorResponse, "description": "NBA head-to-head service timed out."},
    },
    operation_id="getMatchupHistory",
)
def get_matchup_history(
    response: Response,
    team1_id: int = Path(..., description="First NBA team identifier.", example=1610612755),
    team2_id: int = Path(..., description="Second NBA team identifier.", example=1610612753),
    _=Depends(get_current_user),
):
    _validate_matchup(team1_id, team2_id)
    games, cache_status = nba_service.get_h2h_with_cache_status(team1_id, team2_id)
    cache_service.apply_cache_headers(response, cache_status, nba_service.H2H_CACHE_TTL)
    return games


@router.get(
    "/{team1_id}/{team2_id}/top-scorers",
    response_model=TopScorersResponse,
    summary="List scoring leaders for the selected matchup",
    description="Returns the top scorers across the two selected teams only. The frontend can fetch this separately from history or team summaries.",
    responses={
        200: {"description": "Top scorers for the matchup.", "headers": MATCHUP_CACHE_HEADERS},
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        404: {"model": ErrorResponse, "description": "One or both teams were not found."},
        503: {"model": ErrorResponse, "description": "NBA player stats service timed out."},
    },
    operation_id="getMatchupTopScorers",
)
def get_matchup_top_scorers(
    response: Response,
    team1_id: int = Path(..., description="First NBA team identifier.", example=1610612755),
    team2_id: int = Path(..., description="Second NBA team identifier.", example=1610612753),
    limit: int = Query(15, ge=1, le=30, description="Maximum number of players to return.", example=15),
    _=Depends(get_current_user),
):
    _validate_matchup(team1_id, team2_id)
    top_scorers, cache_status = nba_service.get_top_scorers_with_cache_status(
        team1_id, team2_id, limit
    )
    cache_service.apply_cache_headers(response, cache_status, nba_service.PLAYER_STATS_CACHE_TTL)
    return {"top_scorers": top_scorers}


@router.get(
    "/{team1_id}/{team2_id}/top-players",
    response_model=TopPlayersByMetricResponse,
    summary="List category leaders for the selected matchup",
    description="Returns the top players across the two selected teams for points, rebounds, assists, steals, blocks, and turnovers.",
    responses={
        200: {"description": "Top players by metric for the matchup.", "headers": MATCHUP_CACHE_HEADERS},
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        404: {"model": ErrorResponse, "description": "One or both teams were not found."},
        503: {"model": ErrorResponse, "description": "NBA player stats service timed out."},
    },
    operation_id="getMatchupTopPlayers",
)
def get_matchup_top_players(
    response: Response,
    team1_id: int = Path(..., description="First NBA team identifier.", example=1610612755),
    team2_id: int = Path(..., description="Second NBA team identifier.", example=1610612753),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of players to return for each metric.", example=10),
    _=Depends(get_current_user),
):
    _validate_matchup(team1_id, team2_id)
    top_players, cache_status = nba_service.get_top_players_by_metric_with_cache_status(
        team1_id, team2_id, limit
    )
    cache_service.apply_cache_headers(response, cache_status, nba_service.PLAYER_STATS_CACHE_TTL)
    return top_players