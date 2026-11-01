import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("LOLFLEX_DATA", ROOT / "data"))
REPORTS_DIR = Path(os.getenv("LOLFLEX_REPORTS", ROOT / "reports"))
DB_PATH = DATA_DIR / "lol.sqlite"

load_dotenv(ROOT / ".env")

# JSON consumidos pelo repo de conteúdo (ex.: lol-content/src/data); sem a variável, ficam em data/.
EXPORT_DIR = Path(os.getenv("LOLFLEX_EXPORT", DATA_DIR))

PLATFORM = os.getenv("RIOT_PLATFORM", "br1")
REGION = os.getenv("RIOT_REGION", "americas")
# Limites da chave de desenvolvimento; atualizados automaticamente pelos headers da API.
RATE_SPEC = os.getenv("RIOT_RATE_SPEC", "20:1,100:120")

SOLO = "RANKED_SOLO_5x5"
FLEX = "RANKED_FLEX_SR"
QUEUE_IDS = {SOLO: 420, FLEX: 440}
QUEUE_BY_ID = {v: k for k, v in QUEUE_IDS.items()}
APEX_TIERS = ("challenger", "grandmaster", "master")


def api_key() -> str:
    key = os.getenv("RIOT_API_KEY")
    if not key:
        raise SystemExit("Defina RIOT_API_KEY no arquivo .env (veja .env.example).")
    return key
