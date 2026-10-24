"""Score de desempenho estilo OP Score.

1. Normaliza cada métrica por rota (z-score), com as duas filas juntas para que a régua seja comum.
2. Treina, por rota, uma regressão logística que prevê vitória a partir das métricas do jogador.
3. Score da partida = 10 * P(vitória) prevista fora da amostra (GroupKFold por partida).
4. Score do jogador = média com shrinkage para a média da população (k partidas "fantasmas").

Há dois scores: `score` usa todas as métricas; `score_lane` usa só métricas de rota contra o
oponente direto, que dependem menos do resultado do time (menos vazamento de vitória).
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .config import DATA_DIR, REPORTS_DIR

FULL = ["kda", "deaths_pm", "gold_pm", "cs_pm", "dmg_pm", "vision_pm", "obj_dmg_pm", "kp",
        "dmg_share", "dmg_taken_share", "solo_kills", "gold_pm_diff", "cs_pm_diff",
        "dmg_pm_diff", "vision_pm_diff", "cs10", "max_cs_adv", "max_lvl_lead", "plates"]
LANE = ["cs10", "max_cs_adv", "max_lvl_lead", "vision_adv", "plates", "solo_kills",
        "gold_diff10", "xp_diff10", "cs_diff10", "gold_diff15", "xp_diff15", "cs_diff15"]
SHRINK_K = 10


def _fit_role(d: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, float, pd.Series]:
    cols = [c for c in cols if c in d and d[c].notna().mean() > 0.8]
    X = d[cols].astype(float).fillna(d[cols].median())
    y = d["win"].to_numpy()
    oof = np.zeros(len(d))
    folds = GroupKFold(n_splits=5)
    for tr, te in folds.split(X, y, groups=d["match_id"]):
        model = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000))
        model.fit(X.iloc[tr], y[tr])
        oof[te] = model.predict_proba(X.iloc[te])[:, 1]
    final = make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000)).fit(X, y)
    weights = pd.Series(final[-1].coef_[0], index=cols).sort_values(key=abs, ascending=False)
    return oof, roc_auc_score(y, oof), weights


def build() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / "features.parquet")
    df["score"] = np.nan
    df["score_lane"] = np.nan
    lines = ["# Modelo do score", "", "AUC fora da amostra (quanto o score separa vitórias de derrotas):", ""]
    for role, d in df.groupby("role"):
        if len(d) < 200:
            continue
        oof, auc, w = _fit_role(d, FULL)
        df.loc[d.index, "score"] = 10 * oof
        line = f"- **{role}**: score completo AUC={auc:.3f}"
        if d.get("gold_diff15") is not None and d["gold_diff15"].notna().mean() > 0.8:
            oof_l, auc_l, _ = _fit_role(d, LANE)
            df.loc[d.index, "score_lane"] = 10 * oof_l
            line += f"; score de rota AUC={auc_l:.3f}"
        lines += [line, "  - pesos principais: " + ", ".join(f"{k} {v:+.2f}" for k, v in w.head(6).items())]

    df.to_parquet(DATA_DIR / "match_scores.parquet", index=False)
    players = aggregate(df)
    players.to_parquet(DATA_DIR / "player_scores.parquet", index=False)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "score_model.md").write_text("\n".join(lines), encoding="utf-8")
    return players


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for col in ("score", "score_lane"):
        if df[col].isna().all():
            continue
        prior = df[col].mean()
        g = df.dropna(subset=[col]).groupby(["puuid", "queue_id"])[col].agg(["mean", "count"])
        g[f"{col}_shrunk"] = (g["count"] * g["mean"] + SHRINK_K * prior) / (g["count"] + SHRINK_K)
        out.append(g.rename(columns={"mean": f"{col}_mean", "count": f"{col}_n"}))
    return pd.concat(out, axis=1).reset_index()
