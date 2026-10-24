"""Testes B e C com o score de desempenho.

B: o mesmo jogador rende diferente na solo e na flex? (pareado)
C: nas partidas de SOLO, quem é Master+ só na flex rende menos que quem é Master+ na solo,
   controlando pelo elo solo?
"""
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from .config import DATA_DIR, QUEUE_IDS, REPORTS_DIR, SOLO, FLEX
from .ranks import load_players

MIN_MATCHES = 5


def run() -> str:
    scores = pd.read_parquet(DATA_DIR / "player_scores.parquet")
    players = load_players()
    lines = ["# Testes B e C: score de desempenho", ""]

    for col in ("score", "score_lane"):
        if f"{col}_shrunk" not in scores:
            continue
        lines += [f"## Métrica: `{col}`", ""]
        s = scores[scores[f"{col}_n"] >= MIN_MATCHES]
        wide = s.pivot(index="puuid", columns="queue_id", values=f"{col}_mean")

        # B
        paired = wide.dropna(subset=[QUEUE_IDS[SOLO], QUEUE_IDS[FLEX]])
        if len(paired) >= 10:
            diff = paired[QUEUE_IDS[SOLO]] - paired[QUEUE_IDS[FLEX]]
            w = stats.wilcoxon(diff)
            lines += [f"**B**: {len(paired)} jogadores com ≥{MIN_MATCHES} partidas em cada fila. "
                      f"Score médio solo - flex = {diff.mean():+.3f} (Wilcoxon p={w.pvalue:.2g}).", ""]
        else:
            lines += ["**B**: amostra insuficiente.", ""]

        # C
        solo = s[s.queue_id == QUEUE_IDS[SOLO]].set_index("puuid").join(players, how="inner")
        solo["group"] = None
        solo.loc[solo.apex_flex & ~solo.apex_solo, "group"] = "flex_only"
        solo.loc[solo.apex_solo, "group"] = "solo_apex"
        solo = solo.dropna(subset=["group", "value_solo"])
        a = solo.loc[solo.group == "flex_only", f"{col}_shrunk"]
        b = solo.loc[solo.group == "solo_apex", f"{col}_shrunk"]
        if len(a) >= 10 and len(b) >= 10:
            u = stats.mannwhitneyu(a, b, alternative="less")
            fit = smf.ols(f"{col}_shrunk ~ C(group, Treatment('solo_apex')) + value_solo",
                          data=solo).fit()
            coef_name = [c for c in fit.params.index if "flex_only" in c][0]
            lines += [
                f"**C** (partidas de solo): Master+ só na flex n={len(a)}, mediana {a.median():.2f}; "
                f"Master+ na solo n={len(b)}, mediana {b.median():.2f}. "
                f"Mann-Whitney (H1: flex_only menor) p={u.pvalue:.2g}.",
                f"Controlando pelo elo solo (OLS): efeito flex_only = {fit.params[coef_name]:+.3f} "
                f"(p={fit.pvalues[coef_name]:.2g}). Se continua negativo, o jogador rende menos "
                "até do que o elo solo dele sugere.", "",
            ]
        else:
            lines += ["**C**: amostra insuficiente.", ""]

    report = "\n".join(lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "test_bc.md").write_text(report, encoding="utf-8")
    return report
