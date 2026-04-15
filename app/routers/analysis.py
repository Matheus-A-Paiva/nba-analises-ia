from fastapi import APIRouter, Depends, HTTPException, Path

from app.dependencies import get_current_user
from app.schemas.api import AnalysisResponse, ErrorResponse
from app.services import ai_service, nba_service

router = APIRouter(tags=["analysis"])


@router.get(
    "/analysis/{team1_id}/{team2_id}",
    response_model=AnalysisResponse,
    summary="Generate matchup analysis",
    description="Builds a natural-language comparison for two teams using the canonical Gemini-based analysis service and the latest cached NBA team data.",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid bearer token."},
        404: {"model": ErrorResponse, "description": "One or both teams were not found."},
        503: {"model": ErrorResponse, "description": "An upstream NBA stats request timed out."},
    },
    operation_id="getMatchupAnalysis",
)
def get_analysis(
    team1_id: int = Path(..., description="First NBA team identifier.", example=1610612738),
    team2_id: int = Path(..., description="Second NBA team identifier.", example=1610612744),
    _=Depends(get_current_user),
):
    if nba_service.get_team_info(team1_id) is None or nba_service.get_team_info(team2_id) is None:
        raise HTTPException(status_code=404, detail="One or both teams were not found")

    team1 = {
        "info": nba_service.get_team_info(team1_id),
        "stats": nba_service.get_team_stats(team1_id),
    }
    team2 = {
        "info": nba_service.get_team_info(team2_id),
        "stats": nba_service.get_team_stats(team2_id),
    }
    analysis = ai_service.generate_analysis(team1, team2)
    return {"analysis": analysis}
