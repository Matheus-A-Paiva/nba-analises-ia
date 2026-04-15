from datetime import date as DateType

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(..., example="NBA games service timed out. Try again in a moment.")


class TeamInfo(BaseModel):
    id: int = Field(..., example=1610612738)
    name: str = Field(..., example="Boston Celtics")
    abbreviation: str = Field(..., example="BOS")
    logo: str = Field(..., example="https://cdn.nba.com/logos/nba/1610612738/global/L/logo.svg")


class TeamStats(BaseModel):
    points: float = Field(..., example=117.2)
    points_allowed: float = Field(..., example=108.4)
    rebounds: float = Field(..., example=45.8)
    assists: float = Field(..., example=26.9)
    turnovers: float = Field(..., example=12.1)
    fg_pct: float = Field(..., example=48.5)


class PlayerLeader(BaseModel):
    name: str = Field(..., example="Jayson Tatum")
    value: float = Field(..., example=27.1)


class ShootingLeader(BaseModel):
    name: str = Field(..., example="Derrick White")
    percentage: float = Field(..., example=41.8)
    made: float = Field(..., example=3.2)


class TeamLeaders(BaseModel):
    points: PlayerLeader
    rebounds: PlayerLeader
    assists: PlayerLeader
    steals: PlayerLeader
    blocks: PlayerLeader
    turnovers: PlayerLeader
    fg_pct: ShootingLeader | None
    fg3_pct: ShootingLeader | None


class GameResponse(BaseModel):
    game_id: str = Field(..., example="0022501201")
    date: DateType = Field(..., example="2026-04-15")
    time: str = Field(..., example="7:30 PM ET")
    home_team: TeamInfo | None
    away_team: TeamInfo | None


class GameScore(BaseModel):
    home: int = Field(..., example=112)
    away: int = Field(..., example=108)


class HeadToHeadGame(BaseModel):
    date: DateType = Field(..., example="2026-03-10")
    home_team: TeamInfo | None
    away_team: TeamInfo | None
    score: GameScore
    winner: str = Field(..., example="Boston Celtics")


class TeamFullResponse(BaseModel):
    info: TeamInfo | None
    stats: TeamStats
    players: TeamLeaders


class TopScorer(BaseModel):
    player_id: int = Field(..., example=1628369)
    name: str = Field(..., example="Jayson Tatum")
    team_id: int = Field(..., example=1610612738)
    team: str = Field(..., example="Boston Celtics")
    team_abbreviation: str = Field(..., example="BOS")
    points: float = Field(..., example=27.1)
    photo: str = Field(..., example="https://cdn.nba.com/headshots/nba/latest/1040x760/1628369.png")


class MetricPlayer(BaseModel):
    player_id: int = Field(..., example=1628369)
    name: str = Field(..., example="Jayson Tatum")
    team_id: int = Field(..., example=1610612738)
    team: str = Field(..., example="Boston Celtics")
    team_abbreviation: str = Field(..., example="BOS")
    value: float = Field(..., example=8.3)
    photo: str = Field(..., example="https://cdn.nba.com/headshots/nba/latest/1040x760/1628369.png")


class TopPlayersByMetricResponse(BaseModel):
    points: list[MetricPlayer]
    rebounds: list[MetricPlayer]
    assists: list[MetricPlayer]
    steals: list[MetricPlayer]
    blocks: list[MetricPlayer]
    turnovers: list[MetricPlayer]


class TopScorersResponse(BaseModel):
    top_scorers: list[TopScorer]


class AnalysisResponse(BaseModel):
    analysis: str = Field(..., example="Boston chega melhor no geral pelo volume ofensivo e pela defesa mais consistente. O adversário tem chance se controlar melhor os turnovers e dominar os rebotes. Hoje, Boston aparece como favorito.")