from fastapi import APIRouter, Depends, HTTPException, Path

from app.dependencies import get_current_user
from app.schemas.api import ErrorResponse, TeamFullResponse
from app.services import nba_service

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get(
    "/{team_id}",
    response_model=TeamFullResponse,
    summary="Get one team summary",
    description="Returns the reusable team payload for matchup and detail screens, including basic team info, season stats, and team leaders.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        404: {"model": ErrorResponse, "description": "Team not found."},
        503: {"model": ErrorResponse, "description": "An upstream NBA stats request timed out."},
    },
    operation_id="getTeamSummary",
)
def get_team(
    team_id: int = Path(..., description="NBA team identifier.", example=1610612755),
    _=Depends(get_current_user),
):
    team_info = nba_service.get_team_info(team_id)
    if team_info is None:
        raise HTTPException(status_code=404, detail="Team not found")

    return nba_service.get_team_full(team_id)