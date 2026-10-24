"""Conversão de elo para escala numérica e carga das tabelas de elo."""
import pandas as pd

from . import config
from .db import connect

TIERS = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"]
APEX = {"MASTER", "GRANDMASTER", "CHALLENGER"}
DIVISIONS = {"IV": 0, "III": 1, "II": 2, "I": 3}
MASTER_FLOOR = 400 * len(TIERS)  # 2800: Master 0 LP
DIAMOND_FLOOR = 400 * TIERS.index("DIAMOND")  # 2400


def rank_value(tier: str | None, division: str | None, lp: float | None) -> float:
    """Ferro IV 0 LP = 0; cada divisão vale 100; Master+ = 2800 + LP (contínuo)."""
    if tier is None or pd.isna(tier):
        return float("nan")
    if tier in APEX:
        return MASTER_FLOOR + lp
    return 400 * TIERS.index(tier) + 100 * DIVISIONS[division] + lp


def load_players() -> pd.DataFrame:
    """Uma linha por jogador high elo, com elo e nº de partidas nas duas filas."""
    con = connect()
    ranks = pd.read_sql("SELECT * FROM ranks", con)
    apex = pd.read_sql("SELECT puuid, queue FROM apex", con)
    fetched = pd.read_sql("SELECT puuid FROM rank_fetch", con)

    ranks["value"] = [rank_value(t, d, lp) for t, d, lp in zip(ranks.tier, ranks.division, ranks.lp)]
    ranks["games"] = ranks.wins + ranks.losses
    parts = []
    for col in ("value", "games", "tier"):
        w = ranks.pivot(index="puuid", columns="queue", values=col)
        if col != "tier":
            w = w.astype(float)
        w.columns = [f"{col}_{'solo' if q == config.SOLO else 'flex'}" for q in w.columns]
        parts.append(w)
    wide = pd.concat(parts, axis=1)

    players = fetched.set_index("puuid").join(wide, how="left")
    for col in ("value_solo", "value_flex", "games_solo", "games_flex", "tier_solo", "tier_flex"):
        if col not in players:
            players[col] = float("nan")
    players["apex_solo"] = players.index.isin(apex.loc[apex.queue == config.SOLO, "puuid"])
    players["apex_flex"] = players.index.isin(apex.loc[apex.queue == config.FLEX, "puuid"])
    return players
