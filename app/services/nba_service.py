import logging
from datetime import date, timedelta

import pandas as pd
from curl_cffi import requests as curl_requests
from nba_api.stats.static import teams
from nba_api.stats.library.http import STATS_HEADERS

from app.services import cache_service

logger = logging.getLogger(__name__)

NBA_SCOREBOARD_TIMEOUT = 12
NBA_TEAM_STATS_TIMEOUT = 10
NBA_PLAYER_STATS_TIMEOUT = 10
NBA_GAME_FINDER_TIMEOUT = 10

GAMES_BY_DATE_CACHE_TTL = timedelta(minutes=10)
TEAM_STATS_CACHE_TTL = timedelta(minutes=30)
PLAYER_STATS_CACHE_TTL = timedelta(minutes=10)
TOP_SCORERS_CACHE_TTL = timedelta(minutes=10)
H2H_CACHE_TTL = timedelta(hours=6)

NBA_BROWSER_IMPERSONATION = "chrome124"

TEAM_STATS_PARAMS = {
    "College": "",
    "Conference": "",
    "DateFrom": "",
    "DateTo": "",
    "Division": "",
    "GameScope": "",
    "GameSegment": "",
    "Height": "",
    "LastNGames": "0",
    "LeagueID": "00",
    "Location": "",
    "MeasureType": "Base",
    "Month": "0",
    "OpponentTeamID": "0",
    "Outcome": "",
    "PORound": "0",
    "PaceAdjust": "N",
    "PerMode": "PerGame",
    "Period": "0",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "PlusMinus": "N",
    "Rank": "N",
    "Season": "2025-26",
    "SeasonSegment": "",
    "SeasonType": "Regular Season",
    "ShotClockRange": "",
    "StarterBench": "",
    "TeamID": "0",
    "TwoWay": "0",
    "VsConference": "",
    "VsDivision": "",
    "Weight": "",
}

PLAYER_STATS_PARAMS = {
    "College": "",
    "Conference": "",
    "Country": "",
    "DateFrom": "",
    "DateTo": "",
    "Division": "",
    "DraftPick": "",
    "DraftYear": "",
    "GameScope": "",
    "GameSegment": "",
    "Height": "",
    "LastNGames": "0",
    "LeagueID": "00",
    "Location": "",
    "MeasureType": "Base",
    "Month": "0",
    "OpponentTeamID": "0",
    "Outcome": "",
    "PORound": "0",
    "PaceAdjust": "N",
    "PerMode": "Totals",
    "Period": "0",
    "PlayerExperience": "",
    "PlayerPosition": "",
    "PlusMinus": "N",
    "Rank": "N",
    "Season": "2025-26",
    "SeasonSegment": "",
    "SeasonType": "Regular Season",
    "ShotClockRange": "",
    "StarterBench": "",
    "TeamID": "0",
    "TwoWay": "0",
    "VsConference": "",
    "VsDivision": "",
    "Weight": "",
}

MATCHUP_HISTORY_PARAMS = {
    "PlayerOrTeam": "T",
    "LeagueID": "00",
    "Season": TEAM_STATS_PARAMS["Season"],
    "SeasonType": TEAM_STATS_PARAMS["SeasonType"],
}


def get_team_info(team_id: int) -> dict | None:
    for t in teams.get_teams():
        if t["id"] == team_id:
            return {
                "id": team_id,
                "name": t["full_name"],
                "abbreviation": t["abbreviation"],
                "logo": f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg",
            }
    return None


def get_player_photo(player_id) -> str:
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(player_id)}.png"


def _get_result_set_dataframe(endpoint: str, params: dict[str, str], timeout: int) -> pd.DataFrame:
    response = curl_requests.get(
        f"https://stats.nba.com/stats/{endpoint}",
        params=params,
        headers=STATS_HEADERS,
        timeout=timeout,
        impersonate=NBA_BROWSER_IMPERSONATION,
    )
    response.raise_for_status()
    payload = response.json()

    result_sets = payload.get("resultSets") or []
    if not result_sets:
        result_set = payload.get("resultSet")
        if isinstance(result_set, dict):
            result_sets = [result_set]

    if not result_sets:
        return pd.DataFrame()

    first_result = result_sets[0]
    return pd.DataFrame(first_result.get("rowSet", []), columns=first_result.get("headers", []))


def get_league_team_stats_df():
    df, _ = cache_service.get_cached_resource(
        cache_key="league-team-stats",
        ttl=TEAM_STATS_CACHE_TTL,
        fetcher=lambda: _get_result_set_dataframe(
            endpoint="leaguedashteamstats",
            params=TEAM_STATS_PARAMS,
            timeout=NBA_TEAM_STATS_TIMEOUT,
        ),
        label="league team stats",
        error_detail="NBA team stats service timed out. Try again in a moment.",
    )
    return df


def get_league_player_stats_df():
    df, _ = cache_service.get_cached_resource(
        cache_key="league-player-stats",
        ttl=PLAYER_STATS_CACHE_TTL,
        fetcher=lambda: _get_result_set_dataframe(
            endpoint="leaguedashplayerstats",
            params=PLAYER_STATS_PARAMS,
            timeout=NBA_PLAYER_STATS_TIMEOUT,
        ),
        label="league player stats",
        error_detail="NBA player stats service timed out. Try again in a moment.",
    )
    return df


def get_league_player_stats_df_with_cache_status() -> tuple[pd.DataFrame, str]:
    df, cache_status = cache_service.get_cached_resource(
        cache_key="league-player-stats",
        ttl=PLAYER_STATS_CACHE_TTL,
        fetcher=lambda: _get_result_set_dataframe(
            endpoint="leaguedashplayerstats",
            params=PLAYER_STATS_PARAMS,
            timeout=NBA_PLAYER_STATS_TIMEOUT,
        ),
        label="league player stats",
        error_detail="NBA player stats service timed out. Try again in a moment.",
    )
    return df, cache_status


def get_team_stats(team_id: int) -> dict:
    df = get_league_team_stats_df()
    team = df[df["TEAM_ID"] == team_id].iloc[0]

    return {
        "points": round(float(team["PTS"]), 1),
        "points_allowed": round(float(team["PTS"] - team["PLUS_MINUS"]), 1),
        "rebounds": round(float(team["REB"]), 1),
        "assists": round(float(team["AST"]), 1),
        "turnovers": round(float(team["TOV"]), 1),
        "fg_pct": round(team["FG_PCT"] * 100, 1),
    }


def get_best_players(team_id: int) -> dict:
    df = get_league_player_stats_df()
    team_df = df[df["TEAM_ID"] == team_id].copy()

    if team_df.empty:
        return {}

    team_df["PTS_PG"] = team_df["PTS"] / team_df["GP"]
    team_df["REB_PG"] = team_df["REB"] / team_df["GP"]
    team_df["AST_PG"] = team_df["AST"] / team_df["GP"]
    team_df["STL_PG"] = team_df["STL"] / team_df["GP"]
    team_df["BLK_PG"] = team_df["BLK"] / team_df["GP"]
    team_df["TOV_PG"] = team_df["TOV"] / team_df["GP"]

    valid_fg = team_df[team_df["FGA"] >= 5]
    valid_3pt = team_df[team_df["FG3A"] >= 2]

    def pick_pg(col):
        p = team_df.sort_values(col, ascending=False).iloc[0]
        return {"name": p["PLAYER_NAME"], "value": round(float(p[col]), 1)}

    def pick_fg(df_base):
        if df_base.empty:
            return None
        df_base = df_base.copy()
        df_base["FGM_PG"] = df_base["FGM"] / df_base["GP"]
        df_base["score"] = df_base["FG_PCT"] * df_base["FGM_PG"]
        p = df_base.sort_values("score", ascending=False).iloc[0]
        return {
            "name": p["PLAYER_NAME"],
            "percentage": round(p["FG_PCT"] * 100, 1),
            "made": round(p["FGM_PG"], 1),
        }

    def pick_fg3(df_base):
        if df_base.empty:
            return None
        df_base = df_base.copy()
        df_base["FG3M_PG"] = df_base["FG3M"] / df_base["GP"]
        df_base["score"] = df_base["FG3_PCT"] * df_base["FG3M_PG"]
        p = df_base.sort_values("score", ascending=False).iloc[0]
        return {
            "name": p["PLAYER_NAME"],
            "percentage": round(p["FG3_PCT"] * 100, 1),
            "made": round(p["FG3M_PG"], 1),
        }

    return {
        "points": pick_pg("PTS_PG"),
        "rebounds": pick_pg("REB_PG"),
        "assists": pick_pg("AST_PG"),
        "steals": pick_pg("STL_PG"),
        "blocks": pick_pg("BLK_PG"),
        "turnovers": pick_pg("TOV_PG"),
        "fg_pct": pick_fg(valid_fg),
        "fg3_pct": pick_fg3(valid_3pt),
    }


def _fetch_h2h_games(team1_id: int, team2_id: int) -> list:
    df = _get_result_set_dataframe(
        endpoint="leaguegamefinder",
        params={
            **MATCHUP_HISTORY_PARAMS,
            "TeamID": str(team1_id),
            "VsTeamID": str(team2_id),
        },
        timeout=NBA_GAME_FINDER_TIMEOUT,
    )

    if df.empty:
        return []

    team1 = get_team_info(team1_id)
    team2 = get_team_info(team2_id)

    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values("GAME_DATE", ascending=False).head(5)

    games = []
    for _, row in df.iterrows():
        matchup = row["MATCHUP"]
        team1_pts = int(row["PTS"])
        team2_pts = int(row["PTS"] - row["PLUS_MINUS"])

        if "vs." in matchup:
            home, away = team1, team2
            home_pts, away_pts = team1_pts, team2_pts
        else:
            home, away = team2, team1
            home_pts, away_pts = team2_pts, team1_pts

        winner = team1["name"] if row["WL"] == "W" else team2["name"]

        games.append(
            {
                "date": row["GAME_DATE"].strftime("%Y-%m-%d"),
                "home_team": home,
                "away_team": away,
                "score": {"home": home_pts, "away": away_pts},
                "winner": winner,
            }
        )

    return games


def get_h2h(team1_id: int, team2_id: int) -> list:
    cache_team1_id, cache_team2_id = sorted((team1_id, team2_id))
    games, _ = cache_service.get_cached_resource(
        cache_key=f"h2h:{cache_team1_id}:{cache_team2_id}",
        ttl=H2H_CACHE_TTL,
        fetcher=lambda: _fetch_h2h_games(team1_id, team2_id),
        label=f"head-to-head {team1_id}-{team2_id}",
        error_detail="NBA head-to-head service timed out. Try again in a moment.",
    )
    return games


def get_h2h_with_cache_status(team1_id: int, team2_id: int) -> tuple[list, str]:
    cache_team1_id, cache_team2_id = sorted((team1_id, team2_id))
    return cache_service.get_cached_resource(
        cache_key=f"h2h:{cache_team1_id}:{cache_team2_id}",
        ttl=H2H_CACHE_TTL,
        fetcher=lambda: _fetch_h2h_games(team1_id, team2_id),
        label=f"head-to-head {team1_id}-{team2_id}",
        error_detail="NBA head-to-head service timed out. Try again in a moment.",
    )


def get_team_full(team_id: int) -> dict:
    return {
        "info": get_team_info(team_id),
        "stats": get_team_stats(team_id),
        "players": get_best_players(team_id),
    }


def get_top_scorers(team1_id: int, team2_id: int, limit: int = 15) -> list:
    df = get_league_player_stats_df()
    filtered = df[df["TEAM_ID"].isin([team1_id, team2_id])].copy()

    if filtered.empty:
        return []

    filtered = filtered[filtered["GP"] > 0].copy()
    filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]

    team_map = {
        team1_id: get_team_info(team1_id),
        team2_id: get_team_info(team2_id),
    }

    top = filtered.sort_values("PTS_PG", ascending=False).head(limit)

    result = []
    for _, row in top.iterrows():
        team = team_map.get(int(row["TEAM_ID"]))
        result.append(
            {
                "player_id": int(row["PLAYER_ID"]),
                "name": row["PLAYER_NAME"],
                "team_id": int(row["TEAM_ID"]),
                "team": team["name"] if team else "",
                "team_abbreviation": team["abbreviation"] if team else "",
                "points": round(float(row["PTS_PG"]), 1),
                "photo": get_player_photo(row["PLAYER_ID"]),
            }
        )

    return result


def get_top_scorers_with_cache_status(
    team1_id: int, team2_id: int, limit: int = 15
) -> tuple[list, str]:
    df, cache_status = get_league_player_stats_df_with_cache_status()
    filtered = df[df["TEAM_ID"].isin([team1_id, team2_id])].copy()

    if filtered.empty:
        return [], cache_status

    filtered = filtered[filtered["GP"] > 0].copy()
    filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]

    team_map = {
        team1_id: get_team_info(team1_id),
        team2_id: get_team_info(team2_id),
    }

    top = filtered.sort_values("PTS_PG", ascending=False).head(limit)

    result = []
    for _, row in top.iterrows():
        team = team_map.get(int(row["TEAM_ID"]))
        result.append(
            {
                "player_id": int(row["PLAYER_ID"]),
                "name": row["PLAYER_NAME"],
                "team_id": int(row["TEAM_ID"]),
                "team": team["name"] if team else "",
                "team_abbreviation": team["abbreviation"] if team else "",
                "points": round(float(row["PTS_PG"]), 1),
                "photo": get_player_photo(row["PLAYER_ID"]),
            }
        )

    return result, cache_status


def get_top_players_by_metric(team1_id: int, team2_id: int, limit: int = 10) -> dict:
    df = get_league_player_stats_df()
    filtered = df[df["TEAM_ID"].isin([team1_id, team2_id])].copy()

    if filtered.empty:
        return {
            "points": [],
            "rebounds": [],
            "assists": [],
            "steals": [],
            "blocks": [],
            "turnovers": [],
        }

    filtered = filtered[filtered["GP"] > 0].copy()
    filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]
    filtered["REB_PG"] = filtered["REB"] / filtered["GP"]
    filtered["AST_PG"] = filtered["AST"] / filtered["GP"]
    filtered["STL_PG"] = filtered["STL"] / filtered["GP"]
    filtered["BLK_PG"] = filtered["BLK"] / filtered["GP"]
    filtered["TOV_PG"] = filtered["TOV"] / filtered["GP"]

    team_map = {
        team1_id: get_team_info(team1_id),
        team2_id: get_team_info(team2_id),
    }

    metric_map = {
        "points": "PTS_PG",
        "rebounds": "REB_PG",
        "assists": "AST_PG",
        "steals": "STL_PG",
        "blocks": "BLK_PG",
        "turnovers": "TOV_PG",
    }

    result = {}
    for metric_name, column in metric_map.items():
        top = filtered.sort_values(column, ascending=False).head(limit)
        result[metric_name] = []
        for _, row in top.iterrows():
            team = team_map.get(int(row["TEAM_ID"]))
            result[metric_name].append(
                {
                    "player_id": int(row["PLAYER_ID"]),
                    "name": row["PLAYER_NAME"],
                    "team_id": int(row["TEAM_ID"]),
                    "team": team["name"] if team else "",
                    "team_abbreviation": team["abbreviation"] if team else "",
                    "value": round(float(row[column]), 1),
                    "photo": get_player_photo(row["PLAYER_ID"]),
                }
            )

    return result


def get_top_players_by_metric_with_cache_status(
    team1_id: int, team2_id: int, limit: int = 10
) -> tuple[dict, str]:
    df, cache_status = get_league_player_stats_df_with_cache_status()
    filtered = df[df["TEAM_ID"].isin([team1_id, team2_id])].copy()

    if filtered.empty:
        return {
            "points": [],
            "rebounds": [],
            "assists": [],
            "steals": [],
            "blocks": [],
            "turnovers": [],
        }, cache_status

    filtered = filtered[filtered["GP"] > 0].copy()
    filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]
    filtered["REB_PG"] = filtered["REB"] / filtered["GP"]
    filtered["AST_PG"] = filtered["AST"] / filtered["GP"]
    filtered["STL_PG"] = filtered["STL"] / filtered["GP"]
    filtered["BLK_PG"] = filtered["BLK"] / filtered["GP"]
    filtered["TOV_PG"] = filtered["TOV"] / filtered["GP"]

    team_map = {
        team1_id: get_team_info(team1_id),
        team2_id: get_team_info(team2_id),
    }

    metric_map = {
        "points": "PTS_PG",
        "rebounds": "REB_PG",
        "assists": "AST_PG",
        "steals": "STL_PG",
        "blocks": "BLK_PG",
        "turnovers": "TOV_PG",
    }

    result = {}
    for metric_name, column in metric_map.items():
        top = filtered.sort_values(column, ascending=False).head(limit)
        result[metric_name] = []
        for _, row in top.iterrows():
            team = team_map.get(int(row["TEAM_ID"]))
            result[metric_name].append(
                {
                    "player_id": int(row["PLAYER_ID"]),
                    "name": row["PLAYER_NAME"],
                    "team_id": int(row["TEAM_ID"]),
                    "team": team["name"] if team else "",
                    "team_abbreviation": team["abbreviation"] if team else "",
                    "value": round(float(row[column]), 1),
                    "photo": get_player_photo(row["PLAYER_ID"]),
                }
            )

    return result, cache_status


def get_top_scorers_global(
    limit: int = 15, with_cache_status: bool = False
) -> list | tuple[list, str]:
    def fetch_top_scorers():
        df = get_league_player_stats_df()

        if df.empty:
            return []

        filtered = df[df["GP"] > 0].copy()
        filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]

        team_lookup = {t["id"]: t for t in teams.get_teams()}
        top = filtered.sort_values("PTS_PG", ascending=False).head(limit)

        result = []
        for _, row in top.iterrows():
            team = team_lookup.get(int(row["TEAM_ID"]), {})
            result.append(
                {
                    "player_id": int(row["PLAYER_ID"]),
                    "name": row["PLAYER_NAME"],
                    "team_id": int(row["TEAM_ID"]),
                    "team": team.get("full_name", ""),
                    "team_abbreviation": team.get("abbreviation", ""),
                    "points": round(float(row["PTS_PG"]), 1),
                    "photo": get_player_photo(row["PLAYER_ID"]),
                }
            )

        return result

    result, cache_status = cache_service.get_cached_resource(
        cache_key=f"top-scorers-global:{limit}",
        ttl=TOP_SCORERS_CACHE_TTL,
        fetcher=fetch_top_scorers,
        label=f"global top scorers limit={limit}",
        error_detail="NBA player stats service timed out. Try again in a moment.",
    )

    if with_cache_status:
        return result, cache_status

    return result


def get_games_by_date(
    game_date: date, with_cache_status: bool = False
) -> list | tuple[list, str]:
    def fetch_games():
        formatted_date = game_date.strftime("%m/%d/%Y")
        df = _get_result_set_dataframe(
            endpoint="scoreboardv2",
            params={
                "DayOffset": "0",
                "GameDate": formatted_date,
                "LeagueID": "00",
            },
            timeout=NBA_SCOREBOARD_TIMEOUT,
        )

        games = []
        for _, row in df.iterrows():
            games.append(
                {
                    "game_id": str(row["GAME_ID"]),
                    "date": game_date.isoformat(),
                    "time": row["GAME_STATUS_TEXT"],
                    "home_team": get_team_info(row["HOME_TEAM_ID"]),
                    "away_team": get_team_info(row["VISITOR_TEAM_ID"]),
                }
            )

        return games

    games, cache_status = cache_service.get_cached_resource(
        cache_key=f"games:{game_date.isoformat()}",
        ttl=GAMES_BY_DATE_CACHE_TTL,
        fetcher=fetch_games,
        label=f"games for {game_date.isoformat()}",
        error_detail="NBA games service timed out. Try again in a moment.",
    )

    if with_cache_status:
        return games, cache_status

    return games
