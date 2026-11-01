"""Dataset público: as tabelas que a análise usa, sem identificar jogadores nem partidas.

PUUIDs e IDs de partida viram pseudônimos sequenciais (p00001, m00001) na mesma ordem dos originais,
para que ordenações, GroupKFold e amostras com semente deem exatamente os mesmos números.
O JSON bruto da Riot não sai: `matches` e `timelines` levam só os IDs. Com o dataset dá para rodar
test-a, score, test-bc, studies e perf; só `features` (que lê o JSON) fica de fora.
"""
import sqlite3
import zipfile
from datetime import date
from pathlib import Path

import pandas as pd

from .config import DATA_DIR, DB_PATH, ROOT
from .db import SCHEMA

TABLES = ["apex", "ranks", "rank_fetch", "rank_history", "match_ids", "match_fetch"]
PARQUETS = ["features", "match_scores", "player_scores"]


def _codes(values: pd.Series, prefix: str) -> dict[str, str]:
    ordered = sorted(set(values.dropna()))
    width = len(str(len(ordered)))
    return {v: f"{prefix}{i:0{width}d}" for i, v in enumerate(ordered, 1)}


def build(out_dir: Path = DATA_DIR / "public") -> Path:
    src = sqlite3.connect(DB_PATH)
    # ORDER BY rowid: as consultas sem ORDER BY da análise devolvem as linhas na ordem de inserção.
    tables = {t: pd.read_sql(f"SELECT * FROM {t} ORDER BY rowid", src) for t in TABLES}
    tables["matches"] = pd.read_sql("SELECT match_id, queue_id FROM matches ORDER BY rowid", src)
    tables["timelines"] = pd.read_sql("SELECT match_id FROM timelines ORDER BY rowid", src)
    frames = {f: pd.read_parquet(DATA_DIR / f"{f}.parquet") for f in PARQUETS}

    everything = [*tables.values(), *frames.values()]
    codes = {"puuid": _codes(pd.concat([d.puuid for d in everything if "puuid" in d]), "p"),
             "match_id": _codes(pd.concat([d.match_id for d in everything if "match_id" in d]), "m")}

    def anon(d: pd.DataFrame) -> pd.DataFrame:
        d = d.copy()
        for col, mapping in codes.items():
            if col in d:
                d[col] = d[col].map(mapping)
        originals = set(codes["puuid"]) | set(codes["match_id"])
        leaked = [c for c in d.select_dtypes("object") if d[c].isin(originals).any()]
        assert not leaked, f"identificadores originais em {leaked}"
        return d

    stage = out_dir / "dataset"
    stage.mkdir(parents=True, exist_ok=True)
    db = stage / "lol.sqlite"
    db.unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    for name, d in tables.items():
        d = anon(d)
        if name in ("matches", "timelines"):
            d["data"] = None
        d.to_sql(name, con, if_exists="append", index=False)
    con.commit()
    con.execute("VACUUM")
    con.close()
    for f, d in frames.items():
        anon(d).to_parquet(stage / f"{f}.parquet", index=False)

    path = out_dir / f"lol-data-dataset-{date.today()}.zip"
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ROOT / "DATASET.md", "DATASET.md")
        for p in sorted(stage.iterdir()):
            z.write(p, p.name)
    return path
