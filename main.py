from fastapi import FastAPI
from datetime import datetime, timedelta
from nba_api.stats.static import teams
from nba_api.stats.endpoints import (
    leaguedashteamstats,
    leaguedashplayerstats,
    leaguegamefinder,
    scoreboardv2
)
import pandas as pd
import requests

app = FastAPI()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3:8b"


# HELPERS
def get_team_info(team_id):
    for t in teams.get_teams():
        if t["id"] == team_id:
            return {
                "id": team_id,
                "name": t["full_name"],
                "abbreviation": t["abbreviation"],
                "logo": f"https://cdn.nba.com/logos/nba/{team_id}/global/L/logo.svg"
            }


def get_player_photo(player_id):
    return f"https://cdn.nba.com/headshots/nba/latest/1040x760/{int(player_id)}.png"


# TEAM STATS (PER GAME)
def get_team_stats(team_id):
    df = leaguedashteamstats.LeagueDashTeamStats().get_data_frames()[0]
    team = df[df["TEAM_ID"] == team_id].iloc[0]
    gp = team["GP"]

    return {
        "points": round(team["PTS"] / gp, 1),
        "points_allowed": round((team["PTS"] - team["PLUS_MINUS"]) / gp, 1),
        "rebounds": round(team["REB"] / gp, 1),
        "assists": round(team["AST"] / gp, 1),
        "turnovers": round(team["TOV"] / gp, 1),
        "fg_pct": round(team["FG_PCT"] * 100, 1)
    }



# BEST PLAYERS 
def get_best_players(team_id):
    df = leaguedashplayerstats.LeagueDashPlayerStats().get_data_frames()[0]
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
        return {
            "name": p["PLAYER_NAME"],
            "value": round(float(p[col]), 1)
        }

    def pick_fg(df_base):
        if df_base.empty:
            return None

        df_base = df_base.copy()
        df_base["FGM_PG"] = df_base["FGM"] / df_base["GP"]

        # score real (qualidade + volume)
        df_base["score"] = df_base["FG_PCT"] * df_base["FGM_PG"]

        p = df_base.sort_values("score", ascending=False).iloc[0]

        return {
            "name": p["PLAYER_NAME"],
            "percentage": round(p["FG_PCT"] * 100, 1),
            "made": round(p["FGM_PG"], 1)
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
            "made": round(p["FG3M_PG"], 1)
        }

    return {
        "points": pick_pg("PTS_PG"),
        "rebounds": pick_pg("REB_PG"),
        "assists": pick_pg("AST_PG"),
        "steals": pick_pg("STL_PG"),
        "blocks": pick_pg("BLK_PG"),
        "turnovers": pick_pg("TOV_PG"),
        "fg_pct": pick_fg(valid_fg),
        "fg3_pct": pick_fg3(valid_3pt)
    }


# HEAD TO HEAD
def get_h2h(team1_id, team2_id):
    df = leaguegamefinder.LeagueGameFinder(
        team_id_nullable=team1_id,
        vs_team_id_nullable=team2_id
    ).get_data_frames()[0]

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
            home = team1
            away = team2
            home_pts = team1_pts
            away_pts = team2_pts
        else:
            home = team2
            away = team1
            home_pts = team2_pts
            away_pts = team1_pts

        winner = team1["name"] if row["WL"] == "W" else team2["name"]

        games.append({
            "date": row["GAME_DATE"].strftime("%Y-%m-%d"),
            "home_team": home,
            "away_team": away,
            "score": {
                "home": home_pts,
                "away": away_pts
            },
            "winner": winner
        })

    return games


# TEAM FULL
def get_team_full(team_id):
    return {
        "info": get_team_info(team_id),
        "stats": get_team_stats(team_id),
        "players": get_best_players(team_id)
    }


def get_top_scorers(team1_id, team2_id, limit=15):
    df = leaguedashplayerstats.LeagueDashPlayerStats().get_data_frames()[0]
    filtered = df[df["TEAM_ID"].isin([team1_id, team2_id])].copy()

    if filtered.empty:
        return []

    filtered = filtered[filtered["GP"] > 0].copy()
    filtered["PTS_PG"] = filtered["PTS"] / filtered["GP"]

    team_map = {
        team1_id: get_team_info(team1_id),
        team2_id: get_team_info(team2_id)
    }

    top = filtered.sort_values("PTS_PG", ascending=False).head(limit)

    result = []
    for _, row in top.iterrows():
        team = team_map.get(int(row["TEAM_ID"]))
        result.append({
            "player_id": int(row["PLAYER_ID"]),
            "name": row["PLAYER_NAME"],
            "team_id": int(row["TEAM_ID"]),
            "team": team["name"] if team else "",
            "team_abbreviation": team["abbreviation"] if team else "",
            "points": round(float(row["PTS_PG"]), 1),
            "photo": get_player_photo(row["PLAYER_ID"])
        })

    return result


# UPCOMING GAMES
@app.get("/games/upcoming")
def get_upcoming_games():
    today = datetime.now()
    games = []

    for i in range(3):
        date = (today + timedelta(days=i)).strftime("%m/%d/%Y")

        try:
            sb = scoreboardv2.ScoreboardV2(game_date=date)
            df = sb.get_data_frames()[0]

            for _, row in df.iterrows():
                games.append({
                    "game_id": row["GAME_ID"],
                    "date": date,
                    "time": row["GAME_STATUS_TEXT"],
                    "home_team": get_team_info(row["HOME_TEAM_ID"]),
                    "away_team": get_team_info(row["VISITOR_TEAM_ID"])
                })
        except:
            continue

    return games


# MATCH
@app.get("/match/{team1_id}/{team2_id}")
def get_match(team1_id: int, team2_id: int):
    return {
        "team1": get_team_full(team1_id),
        "team2": get_team_full(team2_id),
        "head_to_head": get_h2h(team1_id, team2_id),
        "top_scorers": get_top_scorers(team1_id, team2_id)
    }


# IA (SEPARADO)
@app.get("/analysis/{team1_id}/{team2_id}")
def get_analysis(team1_id: int, team2_id: int):

    team1 = get_team_full(team1_id)
    team2 = get_team_full(team2_id)

    prompt = f"""
    Responda SOMENTE em português do Brasil.

    Analise os dados abaixo e responda de forma SIMPLES.

    {team1['info']['name']}:
    - Pontos: {team1['stats']['points']}
    - Pontos sofridos: {team1['stats']['points_allowed']}
    - Rebotes: {team1['stats']['rebounds']}
    - Assistências: {team1['stats']['assists']}
    - Turnovers: {team1['stats']['turnovers']}

    {team2['info']['name']}:
    - Pontos: {team2['stats']['points']}
    - Pontos sofridos: {team2['stats']['points_allowed']}
    - Rebotes: {team2['stats']['rebounds']}
    - Assistências: {team2['stats']['assists']}
    - Turnovers: {team2['stats']['turnovers']}

    REGRAS:
    - Menos pontos sofridos = melhor defesa
    - Mais rebotes = vantagem física
    - Menos turnovers = melhor controle
    - NÃO invente nada

    RESPONDA EM 3 A 5 LINHAS:

    - Quem está melhor no geral
    - Principais vantagens de cada time
    - Quem deve vencer
    """
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 120  
            }
        })
        return {"analysis": r.json().get("response", "")}
    except:
        return {"analysis": ""}