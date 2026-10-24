import json
import sqlite3
import zlib

from .config import DATA_DIR, DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS apex (
    puuid TEXT, queue TEXT, tier TEXT, lp INT, wins INT, losses INT, fetched_at TEXT,
    PRIMARY KEY (puuid, queue)
);
CREATE TABLE IF NOT EXISTS ranks (
    puuid TEXT, queue TEXT, tier TEXT, division TEXT, lp INT, wins INT, losses INT,
    PRIMARY KEY (puuid, queue)
);
CREATE TABLE IF NOT EXISTS rank_fetch (puuid TEXT PRIMARY KEY, fetched_at TEXT);
CREATE TABLE IF NOT EXISTS match_ids (
    puuid TEXT, queue_id INT, match_id TEXT, PRIMARY KEY (puuid, match_id)
);
CREATE TABLE IF NOT EXISTS match_fetch (puuid TEXT, queue_id INT, fetched_at TEXT,
    PRIMARY KEY (puuid, queue_id));
CREATE TABLE IF NOT EXISTS matches (match_id TEXT PRIMARY KEY, queue_id INT, data BLOB);
CREATE TABLE IF NOT EXISTS timelines (match_id TEXT PRIMARY KEY, data BLOB);
"""


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript(SCHEMA)
    return con


def pack(obj) -> bytes:
    return zlib.compress(json.dumps(obj, separators=(",", ":")).encode())


def unpack(blob: bytes):
    return json.loads(zlib.decompress(blob))
