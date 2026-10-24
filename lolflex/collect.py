"""Etapas de coleta. Todas são retomáveis: o que já está no banco não é buscado de novo."""
import datetime as dt
import random

from tqdm import tqdm

from . import config
from .db import connect, pack
from .riot import RiotClient


def _client() -> RiotClient:
    return RiotClient(config.api_key(), config.PLATFORM, config.REGION, config.RATE_SPEC)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def collect_leagues() -> None:
    """Master, GM e Challenger das duas filas."""
    client, con = _client(), connect()
    for queue in (config.SOLO, config.FLEX):
        for tier in config.APEX_TIERS:
            league = client.apex_league(tier, queue) or {"entries": []}
            rows = [
                (e["puuid"], queue, league.get("tier", tier.upper()), e["leaguePoints"],
                 e["wins"], e["losses"], _now())
                for e in league["entries"]
            ]
            con.executemany("INSERT OR REPLACE INTO apex VALUES (?,?,?,?,?,?,?)", rows)
            con.commit()
            print(f"{queue:16} {tier:12} {len(rows):5} jogadores")


def collect_ranks(refresh: bool = False) -> None:
    """Elo de cada jogador high elo nas duas filas."""
    client, con = _client(), connect()
    query = "SELECT DISTINCT puuid FROM apex"
    if not refresh:
        query += " WHERE puuid NOT IN (SELECT puuid FROM rank_fetch)"
    puuids = [r[0] for r in con.execute(query)]
    for puuid in tqdm(puuids, desc="elos"):
        entries = client.entries_by_puuid(puuid)
        con.execute("DELETE FROM ranks WHERE puuid = ?", (puuid,))
        for e in entries:
            if e["queueType"] in (config.SOLO, config.FLEX):
                con.execute(
                    "INSERT INTO ranks VALUES (?,?,?,?,?,?,?)",
                    (puuid, e["queueType"], e["tier"], e.get("rank"), e["leaguePoints"],
                     e["wins"], e["losses"]),
                )
        con.execute("INSERT OR REPLACE INTO rank_fetch VALUES (?,?)", (puuid, _now()))
        con.commit()


def collect_matches(sample: int | None, per_queue: int, since_days: int,
                    timelines: bool, seed: int = 42) -> None:
    """Partidas recentes (solo e flex) de uma amostra dos jogadores high elo."""
    client, con = _client(), connect()
    puuids = sorted(r[0] for r in con.execute("SELECT DISTINCT puuid FROM apex"))
    if sample and sample < len(puuids):
        puuids = random.Random(seed).sample(puuids, sample)
    start = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=since_days)).timestamp())

    done = set(con.execute("SELECT puuid, queue_id FROM match_fetch"))
    for puuid in tqdm(puuids, desc="listas de partidas"):
        for queue_id in config.QUEUE_IDS.values():
            if (puuid, queue_id) in done:
                continue
            ids = client.match_ids(puuid, queue_id, per_queue, start)
            con.executemany("INSERT OR IGNORE INTO match_ids VALUES (?,?,?)",
                            [(puuid, queue_id, m) for m in ids])
            con.execute("INSERT OR REPLACE INTO match_fetch VALUES (?,?,?)",
                        (puuid, queue_id, _now()))
            con.commit()

    pending = [r[0] for r in con.execute(
        "SELECT DISTINCT match_id FROM match_ids WHERE match_id NOT IN (SELECT match_id FROM matches)")]
    for match_id in tqdm(pending, desc="partidas"):
        m = client.match(match_id)
        if m:
            con.execute("INSERT OR REPLACE INTO matches VALUES (?,?,?)",
                        (match_id, m["info"]["queueId"], pack(m)))
            con.commit()

    if timelines:
        pending = [r[0] for r in con.execute(
            "SELECT match_id FROM matches WHERE match_id NOT IN (SELECT match_id FROM timelines)")]
        for match_id in tqdm(pending, desc="timelines"):
            t = client.timeline(match_id)
            if t:
                con.execute("INSERT OR REPLACE INTO timelines VALUES (?,?)", (match_id, pack(t)))
                con.commit()
