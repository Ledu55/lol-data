"""Extrai uma linha por (partida, jogador) com métricas por minuto e contra o oponente de rota."""
import pandas as pd
from tqdm import tqdm

from .config import DATA_DIR
from .db import connect, unpack

MIN_DURATION_S = 15 * 60  # descarta remakes e partidas muito curtas
LANE_MINUTES = (10, 15)

CHALLENGES = {
    "kp": "killParticipation",
    "dmg_share": "teamDamagePercentage",
    "dmg_taken_share": "damageTakenOnTeamPercentage",
    "solo_kills": "soloKills",
    "cs10": "laneMinionsFirst10Minutes",
    "max_cs_adv": "maxCsAdvantageOnLaneOpponent",
    "max_lvl_lead": "maxLevelLeadLaneOpponent",
    "vision_adv": "visionScoreAdvantageLaneOpponent",
    "plates": "turretPlatesTaken",
}
PER_MIN = ["gold", "cs", "dmg", "vision", "obj_dmg"]


def _participant_row(match_id, queue_id, minutes, p) -> dict:
    ch = p.get("challenges", {})
    row = {
        "match_id": match_id, "queue_id": queue_id, "puuid": p["puuid"],
        "participant_id": p["participantId"], "team_id": p["teamId"],
        "role": p["teamPosition"], "champion": p["championName"], "win": int(p["win"]),
        "duration_min": minutes,
        "kills": p["kills"], "deaths": p["deaths"], "assists": p["assists"],
        "kda": (p["kills"] + p["assists"]) / max(1, p["deaths"]),
        "deaths_pm": p["deaths"] / minutes,
        "gold_pm": p["goldEarned"] / minutes,
        "cs_pm": (p["totalMinionsKilled"] + p["neutralMinionsKilled"]) / minutes,
        "dmg_pm": p["totalDamageDealtToChampions"] / minutes,
        "vision_pm": p["visionScore"] / minutes,
        "obj_dmg_pm": p["damageDealtToObjectives"] / minutes,
    }
    for col, key in CHALLENGES.items():
        row[col] = ch.get(key)
    return row


def _lane_diffs(timeline, rows_by_pid, opp_of) -> None:
    frames = timeline["info"]["frames"]
    for minute in LANE_MINUTES:
        if minute >= len(frames):
            continue
        pf = frames[minute]["participantFrames"]
        for pid, row in rows_by_pid.items():
            opp = opp_of.get(pid)
            if opp is None:
                continue
            me, them = pf[str(pid)], pf[str(opp)]
            cs = lambda f: f["minionsKilled"] + f["jungleMinionsKilled"]  # noqa: E731
            row[f"gold_diff{minute}"] = me["totalGold"] - them["totalGold"]
            row[f"xp_diff{minute}"] = me["xp"] - them["xp"]
            row[f"cs_diff{minute}"] = cs(me) - cs(them)


def build() -> pd.DataFrame:
    con = connect()
    timelines = {m for (m,) in con.execute("SELECT match_id FROM timelines")}
    rows = []
    cur = con.execute("SELECT match_id, queue_id, data FROM matches")
    for match_id, queue_id, blob in tqdm(cur, desc="features"):
        info = unpack(blob)["info"]
        duration = info["gameDuration"]
        participants = info["participants"]
        if duration < MIN_DURATION_S or any(p.get("gameEndedInEarlySurrender") for p in participants):
            continue
        minutes = duration / 60
        match_rows = {p["participantId"]: _participant_row(match_id, queue_id, minutes, p)
                      for p in participants if p.get("teamPosition")}

        # Oponente de rota: mesma posição, time adversário.
        by_pos = {}
        for pid, r in match_rows.items():
            by_pos.setdefault(r["role"], []).append(pid)
        opp_of = {}
        for pids in by_pos.values():
            if len(pids) == 2 and match_rows[pids[0]]["team_id"] != match_rows[pids[1]]["team_id"]:
                opp_of[pids[0]], opp_of[pids[1]] = pids[1], pids[0]
        for pid, r in match_rows.items():
            opp = opp_of.get(pid)
            for stat in PER_MIN:
                r[f"{stat}_pm_diff"] = r[f"{stat}_pm"] - match_rows[opp][f"{stat}_pm"] if opp else None

        if match_id in timelines:
            (blob_t,) = con.execute("SELECT data FROM timelines WHERE match_id = ?", (match_id,)).fetchone()
            _lane_diffs(unpack(blob_t), match_rows, opp_of)
        rows.extend(match_rows.values())

    df = pd.DataFrame(rows)
    DATA_DIR.mkdir(exist_ok=True)
    df.to_parquet(DATA_DIR / "features.parquet", index=False)
    return df
