"""JSON do vídeo "O elo da flex" (repositório lol-content), em EXPORT_DIR (LOLFLEX_EXPORT).

Os testes A, B e C e os estudos complementares gravam cada um a sua seção no mesmo arquivo. Os valores são os mesmos dos
relatórios em reports/, sem arredondar: o vídeo formata os números na hora de mostrar.
"""
import json
import math

import numpy as np

from .config import EXPORT_DIR

ARQUIVO = EXPORT_DIR / "elo_flex_data.json"


def _limpo(v):
    """Converte tipos do numpy e troca NaN por None, para o JSON ser válido."""
    if isinstance(v, dict):
        return {str(k): _limpo(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [_limpo(x) for x in v]
    if isinstance(v, np.generic):
        v = v.item()
    if isinstance(v, float) and math.isnan(v):
        return None
    return v


def gravar(secao: str, dados: dict) -> None:
    atual = json.loads(ARQUIVO.read_text(encoding="utf-8")) if ARQUIVO.exists() else {}
    atual[secao] = _limpo(dados)
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    ARQUIVO.write_text(json.dumps(atual, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
