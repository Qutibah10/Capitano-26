import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# نحدد مكان ملف .env بناءً على مكان api_sync.py نفسه
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH)

TOKEN = os.getenv("FOOTBALL_DATA_TOKEN")
BASE_URL = "https://api.football-data.org/v4"


def fetch_worldcup_matches():
    """
    Fetch World Cup matches from football-data.org.
    Competition code for FIFA World Cup is usually WC.
    """
    if not TOKEN:
        raise ValueError("FOOTBALL_DATA_TOKEN is missing. Check your .env file.")

    url = f"{BASE_URL}/competitions/WC/matches"

    headers = {
        "X-Auth-Token": TOKEN
    }

    params = {
        "season": 2026
    }

    response = requests.get(url, headers=headers, params=params, timeout=20)

    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")

    data = response.json()
    return data.get("matches", [])


def map_status(status):
    """
    football-data status examples:
    SCHEDULED, TIMED, IN_PLAY, PAUSED, FINISHED, POSTPONED, SUSPENDED, CANCELLED
    """
    status = str(status).upper().strip()

    if status in ["SCHEDULED", "TIMED"]:
        return "SCHEDULED"

    if status in ["IN_PLAY", "PAUSED"]:
        return "LIVE"

    if status == "FINISHED":
        return "FINISHED"

    return "SCHEDULED"


def detect_stage(match):
    """
    Convert football-data stage to our system stage.
    """
    stage = str(match.get("stage", "")).upper().strip()
    group = str(match.get("group", "")).upper().strip()

    if stage == "GROUP_STAGE" or "GROUP" in group:
        return "GROUP"

    if stage in ["LAST_32", "ROUND_OF_32"]:
        return "R32"

    if stage in ["LAST_16", "ROUND_OF_16"]:
        return "R16"

    if stage == "QUARTER_FINALS":
        return "QF"

    if stage == "SEMI_FINALS":
        return "SF"

    if stage == "THIRD_PLACE":
        return "THIRD"

    if stage == "FINAL":
        return "FINAL"

    return stage if stage else "UNKNOWN"


def detect_group(match):
    """
    Extract group letter.
    football-data may return group like GROUP_A.
    """
    group = str(match.get("group", "")).upper().strip()

    if group.startswith("GROUP_"):
        return group.replace("GROUP_", "")

    if group.startswith("GROUP "):
        return group.replace("GROUP ", "")

    return ""


def get_team_names(match):
    home = match.get("homeTeam") or {}
    away = match.get("awayTeam") or {}

    home_name = home.get("name") or home.get("shortName") or "TBD"
    away_name = away.get("name") or away.get("shortName") or "TBD"

    return home_name, away_name


def detect_real_method(match):
    """
    Convert football-data score.duration to our method:
    REGULAR -> NORMAL
    EXTRA_TIME -> ET
    PENALTY_SHOOTOUT -> PEN
    """
    stage = detect_stage(match)

    if stage == "GROUP":
        return "GROUP"

    duration = match.get("score", {}).get("duration")

    if duration == "REGULAR":
        return "NORMAL"

    if duration == "EXTRA_TIME":
        return "ET"

    if duration == "PENALTY_SHOOTOUT":
        return "PEN"

    return "NORMAL"


def detect_real_winner(match):
    """
    For group:
    A / B / DRAW

    For knockout:
    actual winner team name.
    """
    status = map_status(match.get("status", ""))

    if status != "FINISHED":
        return ""

    stage = detect_stage(match)
    home_name, away_name = get_team_names(match)

    score = match.get("score", {})
    winner = score.get("winner")

    # football-data winner is usually HOME_TEAM, AWAY_TEAM, DRAW
    if stage == "GROUP":
        if winner == "HOME_TEAM":
            return "A"
        if winner == "AWAY_TEAM":
            return "B"
        if winner == "DRAW":
            return "DRAW"
        return ""

    # Knockout
    if winner == "HOME_TEAM":
        return home_name

    if winner == "AWAY_TEAM":
        return away_name

    return ""


def convert_utc_to_jordan(utc_date):
    """
    football-data.org returns utcDate in UTC.
    This converts it to Jordan time: Asia/Amman.
    """
    if not utc_date:
        return ""

    try:
        # Example: 2026-06-11T19:00:00Z
        clean_date = str(utc_date).replace("Z", "+00:00")
        utc_dt = datetime.fromisoformat(clean_date)

        jordan_dt = utc_dt.astimezone(ZoneInfo("Asia/Amman"))

        return jordan_dt.strftime("%Y-%m-%d %H:%M")

    except Exception:
        return str(utc_date)[:16].replace("T", " ")


def normalize_match(match):
    """
    Convert football-data match shape to our MatchCache shape.
    """
    match_id = str(match.get("id", ""))

    stage = detect_stage(match)
    group = detect_group(match)

    team_a, team_b = get_team_names(match)

    utc_date = match.get("utcDate", "")
    kickoff = convert_utc_to_jordan(utc_date)

    status = map_status(match.get("status", ""))

    real_winner = ""
    real_method = "GROUP" if stage == "GROUP" else "NORMAL"

    if status == "FINISHED":
        real_winner = detect_real_winner(match)
        real_method = detect_real_method(match)

    return {
        "MatchID": match_id,
        "Stage": stage,
        "Group": group,
        "TeamA": team_a,
        "TeamB": team_b,
        "Kickoff": kickoff,
        "Status": status,
        "RealWinner": real_winner,
        "RealMethod": real_method,
        "LastSynced": ""
    }


def get_normalized_worldcup_matches():
    matches = fetch_worldcup_matches()
    return [normalize_match(m) for m in matches]


def fetch_worldcup_standings():
    """
    Fetch World Cup group standings from football-data.org.
    """
    if not TOKEN:
        raise ValueError("FOOTBALL_DATA_TOKEN is missing. Check your .env file.")

    url = f"{BASE_URL}/competitions/WC/standings"

    headers = {
        "X-Auth-Token": TOKEN
    }

    params = {
        "season": 2026
    }

    response = requests.get(url, headers=headers, params=params, timeout=20)

    if response.status_code != 200:
        raise Exception(f"Standings API Error {response.status_code}: {response.text}")

    data = response.json()
    return data.get("standings", [])


def normalize_group_standings():
    """
    Convert football-data standings to our GroupStandings sheet shape:
    Group | Position | Team

    Important:
    - We only take TOTAL standings.
    - We ignore standings with group = NONE because this is not a real group table.
    - We only keep positions 1 to 4 for each group.
    """
    standings = fetch_worldcup_standings()

    rows = []

    for standing in standings:
        standing_type = str(standing.get("type", "")).upper().strip()

        if standing_type != "TOTAL":
            continue

        group_name = str(standing.get("group", "")).upper().strip()

        if group_name in ["", "NONE", "NULL", "NAN"]:
            continue

        if group_name.startswith("GROUP_"):
            group_name = group_name.replace("GROUP_", "")

        if group_name.startswith("GROUP "):
            group_name = group_name.replace("GROUP ", "")

        table = standing.get("table", [])

        for team_row in table:
            position = team_row.get("position", "")
            team = team_row.get("team", {})
            team_name = team.get("name") or team.get("shortName") or ""

            try:
                position_int = int(position)
            except Exception:
                continue

            if position_int < 1 or position_int > 4:
                continue

            if group_name and team_name:
                rows.append({
                    "Group": group_name,
                    "Position": position_int,
                    "Team": team_name
                })

    return rows