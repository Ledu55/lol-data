"""Teste A: em que elo estão, na outra fila, os jogadores Master+ de cada fila?"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

from .config import REPORTS_DIR
from .ranks import DIAMOND_FLOOR, MASTER_FLOOR, load_players


def _describe(other: pd.Series) -> dict:
    ranked = other.dropna()
    return {
        "jogadores": len(other),
        "sem elo na outra fila": int(other.isna().sum()),
        "mediana outra fila": ranked.median(),
        "% Master+ na outra fila": 100 * (ranked >= MASTER_FLOOR).mean(),
        "% abaixo de Diamante": 100 * (ranked < DIAMOND_FLOOR).mean(),
    }


def _bootstrap_median_diff(a, b, n=5000, seed=0):
    rng = np.random.default_rng(seed)
    diffs = [np.median(rng.choice(a, len(a))) - np.median(rng.choice(b, len(b))) for _ in range(n)]
    return np.percentile(diffs, [2.5, 97.5])


def run(min_games: int = 20) -> str:
    p = load_players()
    flex_group = p[p.apex_flex]
    solo_group = p[p.apex_solo]

    summary = pd.DataFrame({
        "Master+ na FLEX -> elo na solo": _describe(flex_group.value_solo),
        "Master+ na SOLO -> elo na flex": _describe(solo_group.value_flex),
    }).T

    # Gap = elo na própria fila - elo na outra, só entre quem tem partidas suficientes nas duas.
    both = p[(p.games_solo >= min_games) & (p.games_flex >= min_games)]
    gap_flex = (both.loc[both.apex_flex, "value_flex"] - both.loc[both.apex_flex, "value_solo"]).to_numpy()
    gap_solo = (both.loc[both.apex_solo, "value_solo"] - both.loc[both.apex_solo, "value_flex"]).to_numpy()

    lines = ["# Teste A: elo cruzado entre filas", "",
             f"Jogadores com elo consultado: {len(p)}", "",
             summary.round(1).to_markdown(), ""]

    if len(gap_flex) >= 10 and len(gap_solo) >= 10:
        u = stats.mannwhitneyu(gap_flex, gap_solo, alternative="greater")
        lo, hi = _bootstrap_median_diff(gap_flex, gap_solo)
        lines += [
            f"## Queda de elo ao trocar de fila (mín. {min_games} partidas em cada fila)", "",
            f"- Master+ flex: mediana de queda {np.median(gap_flex):.0f} pts (n={len(gap_flex)})",
            f"- Master+ solo: mediana de queda {np.median(gap_solo):.0f} pts (n={len(gap_solo)})",
            f"- Diferença das medianas: {np.median(gap_flex) - np.median(gap_solo):.0f} pts "
            f"(IC95% bootstrap {lo:.0f} a {hi:.0f}); 100 pts = 1 divisão",
            f"- Mann-Whitney (H1: flex cai mais): U={u.statistic:.0f}, p={u.pvalue:.2g}", "",
        ]
        reg = stats.linregress(both.value_flex, both.value_solo)
        lines += [f"Regressão elo_solo ~ elo_flex (n={len(both)}): "
                  f"inclinação {reg.slope:.2f}, intercepto {reg.intercept:.0f}, r={reg.rvalue:.2f}. "
                  "Atenção: a amostra é truncada (só high elo), então use como descrição.", ""]
    else:
        lines += ["Amostra insuficiente para o teste de gaps.", ""]

    REPORTS_DIR.mkdir(exist_ok=True)
    _plot(p)
    lines += ["![elo solo x flex](test_a_scatter.png)"]
    report = "\n".join(lines)
    (REPORTS_DIR / "test_a.md").write_text(report, encoding="utf-8")
    return report


def _plot(p: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(7, 7))
    groups = [
        ("Master+ só na solo", p.apex_solo & ~p.apex_flex, "#2563eb"),
        ("Master+ só na flex", p.apex_flex & ~p.apex_solo, "#dc2626"),
        ("Master+ nas duas", p.apex_solo & p.apex_flex, "#16a34a"),
    ]
    for label, mask, color in groups:
        d = p[mask].dropna(subset=["value_solo", "value_flex"])
        ax.scatter(d.value_flex, d.value_solo, s=8, alpha=0.5, color=color, label=f"{label} (n={len(d)})")
    lim = [0, max(p.value_solo.max(), p.value_flex.max(), MASTER_FLOOR + 100) + 100]
    ax.plot(lim, lim, color="gray", lw=1, ls="--", label="mesmo elo")
    for v in (DIAMOND_FLOOR, MASTER_FLOOR):
        ax.axvline(v, color="lightgray", lw=0.8)
        ax.axhline(v, color="lightgray", lw=0.8)
    ax.set_xlabel("Elo na flex (2400 = Diamante IV, 2800 = Master)")
    ax.set_ylabel("Elo na solo/duo")
    ax.set_title("Elo solo x flex de jogadores high elo (BR)")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(REPORTS_DIR / "test_a_scatter.png", dpi=150)
    plt.close(fig)
