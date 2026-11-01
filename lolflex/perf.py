"""Avaliação de desempenho de jogadores: o que o score mede, quanto confiar nele e o que ele revela.

1. O modelo: AUC e pesos por rota
2. Nota de vitórias e derrotas, e o "MVP da derrota"
3. Uma partida de exemplo
4. Confiabilidade: quantas partidas até a nota de um jogador se estabilizar
5. Nota x elo na solo
6. Perfil do top 10%
7. Campeões
8. O mesmo jogador nas duas filas (resumo dos testes B e estudos)

Gera reports/perf.md e perf_data.json em EXPORT_DIR (LOLFLEX_EXPORT), de onde o repo de conteúdo lê.
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from .config import DATA_DIR, EXPORT_DIR, REPORTS_DIR
from .db import connect, unpack
from .ranks import MASTER_FLOOR, load_players
from .score import FULL, LANE, _fit_role
from .studies import FLEX_ID, SOLO_ID, _paired, _role_z, premade_sizes

ROLES = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
MIN_GAMES = 10
SEED = 7


def _r(x, digits=3):
    return None if pd.isna(x) else round(float(x), digits)


# 1 ----------------------------------------------------------------------------------------------

def model(m: pd.DataFrame) -> dict:
    out = {}
    for role in ROLES:
        d = m[m.role == role]
        _, auc, w = _fit_role(d, FULL)
        _, auc_lane, _ = _fit_role(d, LANE)
        out[role] = {"auc": _r(auc), "auc_lane": _r(auc_lane),
                     "weights": [[k, _r(v)] for k, v in w.items()]}
    return out


# 2 ----------------------------------------------------------------------------------------------

def win_loss(m: pd.DataFrame) -> dict:
    bins = np.arange(0, 10.5, 0.5)
    out = {"bins": bins.tolist()}
    for col in ("score", "score_lane"):
        d = m.dropna(subset=[col])
        hist = {}
        for w, name in ((1, "win"), (0, "loss")):
            h, _ = np.histogram(d.loc[d.win == w, col], bins=bins)
            hist[name] = (h / h.sum()).round(4).tolist()
        # MVP da derrota: a maior nota da partida está no time que perdeu.
        best = d.loc[d.groupby("match_id")[col].idxmax()]
        full = d.groupby("match_id").size()
        best = best[best.match_id.map(full) == 10]
        out[col] = {
            "hist": hist,
            "median_win": _r(d.loc[d.win == 1, col].median(), 2),
            "median_loss": _r(d.loc[d.win == 0, col].median(), 2),
            "loss_above5": _r(100 * (d.loc[d.win == 0, col] >= 5).mean(), 1),
            "win_below5": _r(100 * (d.loc[d.win == 1, col] < 5).mean(), 1),
            "mvp_on_loser": _r(100 * (best.win == 0).mean(), 1),
            "matches": int(len(best)),
        }
    return out


# 3 ----------------------------------------------------------------------------------------------

def example_match(m: pd.DataFrame) -> dict:
    d = m[(m.queue_id == SOLO_ID)].dropna(subset=["score_lane", "gold_diff15"])
    n = d.groupby("match_id").size()
    d = d[d.match_id.map(n) == 10]
    g = d.groupby("match_id")
    # Partida em que o melhor da partida na nota de rota estava no time que perdeu.
    best_lane = d.loc[g.score_lane.idxmax()].set_index("match_id")
    cand = best_lane[(best_lane.win == 0) & (best_lane.score_lane > 8)].index
    dur = g.duration_min.first()
    cand = [c for c in cand if 25 <= dur[c] <= 35]
    rng = np.random.default_rng(SEED)
    match_id = cand[rng.integers(len(cand))]
    x = d[d.match_id == match_id].copy()
    x["role_order"] = x.role.map({r: i for i, r in enumerate(ROLES)})
    x = x.sort_values(["win", "role_order"], ascending=[False, True])
    # Campos crus da API para o destaque da partida (sem nome nem puuid).
    # O dataset público não tem o JSON da Riot; aí o destaque fica vazio.
    (blob,) = connect().execute("SELECT data FROM matches WHERE match_id = ?", (match_id,)).fetchone()
    raw, fields = None, None
    if blob is not None:
        pid = int(best_lane.loc[match_id, "participant_id"])
        p = next(q for q in unpack(blob)["info"]["participants"] if q["participantId"] == pid)
        raw_keys = ["championName", "teamPosition", "kills", "deaths", "assists", "goldEarned",
                    "totalMinionsKilled", "totalDamageDealtToChampions", "visionScore", "win"]
        challenge_keys = ["soloKills", "maxCsAdvantageOnLaneOpponent",
                          "killParticipation", "teamDamagePercentage"]
        raw = {k: p[k] for k in raw_keys}
        raw["challenges"] = {k: _r(p["challenges"][k], 3) for k in challenge_keys}
        fields = len(p) + len(p.get("challenges", {}))
    return {
        "raw": raw,
        "fields": fields,
        "duration": _r(x.duration_min.iloc[0], 1),
        "players": [{
            "win": int(r.win), "role": r.role, "champion": r.champion,
            "k": int(r.kills), "d": int(r.deaths), "a": int(r.assists),
            "gold15": int(r.gold_diff15), "score": _r(r.score, 1), "score_lane": _r(r.score_lane, 1),
        } for r in x.itertuples()],
    }


# 4 ----------------------------------------------------------------------------------------------

STABILITY = ["score", "score_lane", "win", "kda", "deaths_pm", "cs_pm", "dmg_share", "vision_pm",
             "kp", "solo_kills", "cs_diff15", "gold_diff15"]


def reliability(m: pd.DataFrame) -> dict:
    """Correlação entre a média de n partidas e a de outras n partidas do mesmo jogador.

    Métricas brutas entram em z-score por rota, para que trocar de rota não pareça consistência.
    """
    d = m[m.queue_id == SOLO_ID].dropna(subset=["score"])
    counts = d.groupby("puuid").size()
    d = d[d.puuid.map(counts) >= 20]
    raw = [c for c in STABILITY if c not in ("score", "score_lane", "win")]
    z = _role_z(d, raw)
    d = d[["puuid", "score", "score_lane", "win"]].join(z[raw])
    rng = np.random.default_rng(SEED)
    ns = [1, 2, 3, 5, 7, 10]
    curve = {(c, n): [] for c in STABILITY for n in ns}
    for _ in range(30):
        shuffled = d.assign(k=rng.random(len(d))).sort_values(["puuid", "k"])
        shuffled["i"] = shuffled.groupby("puuid").cumcount()
        for n in ns:
            a = shuffled[shuffled.i < n].groupby("puuid")[STABILITY].mean()
            b = shuffled[(shuffled.i >= n) & (shuffled.i < 2 * n)].groupby("puuid")[STABILITY].mean()
            for c in STABILITY:
                curve[c, n].append(a[c].corr(b[c].reindex(a.index)))
    r = {k: float(np.mean(v)) for k, v in curve.items()}

    def projected(c, n):
        # Spearman-Brown a partir de 10 partidas, para mostrar onde a curva chega.
        r10 = r[c, 10]
        r1 = r10 / (10 - 9 * r10)
        return n * r1 / (1 + (n - 1) * r1)

    return {
        "players": int(d.puuid.nunique()),
        "curve": {c: [[n, _r(r[c, n])] for n in ns] for c in ("score", "score_lane", "kda", "cs_pm")},
        "projected": [[n, _r(projected("score", n))] for n in (20, 30, 50)],
        "at10": sorted([[c, _r(r[c, 10])] for c in STABILITY], key=lambda x: -x[1]),
        "shrink_k": 10,
    }


# 5 ----------------------------------------------------------------------------------------------

TIER_GROUPS = [("Esmeralda", lambda t, v: t == "EMERALD"),
               ("Diamante", lambda t, v: t == "DIAMOND"),
               ("Master", lambda t, v: t == "MASTER"),
               ("Grão-Mestre", lambda t, v: t == "GRANDMASTER"),
               ("Desafiante", lambda t, v: t == "CHALLENGER")]


def score_vs_elo(players: pd.DataFrame) -> dict:
    s = pd.read_parquet(DATA_DIR / "player_scores.parquet")
    s = s[(s.queue_id == SOLO_ID) & (s.score_n >= MIN_GAMES)].set_index("puuid")
    x = s.join(players[["value_solo", "tier_solo"]], how="inner").dropna(subset=["value_solo"])
    tiers = []
    for name, f in TIER_GROUPS:
        g = x[[f(t, v) for t, v in zip(x.tier_solo, x.value_solo)]]
        if len(g) >= 20:
            tiers.append({"tier": name, "n": int(len(g)), "median": _r(g.score_shrunk.median(), 2),
                          "q1": _r(g.score_shrunk.quantile(.25), 2), "q3": _r(g.score_shrunk.quantile(.75), 2)})
    apex = x[x.value_solo >= MASTER_FLOOR]
    rho_all = stats.spearmanr(x.value_solo, x.score_shrunk)
    rho_apex = stats.spearmanr(apex.value_solo, apex.score_shrunk)
    rng = np.random.default_rng(SEED)
    pts = x.sample(min(900, len(x)), random_state=SEED)
    return {
        "players": int(len(x)),
        "rho_all": _r(rho_all.statistic), "p_all": float(f"{rho_all.pvalue:.2g}"),
        "rho_apex": _r(rho_apex.statistic), "p_apex": float(f"{rho_apex.pvalue:.2g}"),
        "apex_players": int(len(apex)),
        "tiers": tiers,
        # Jitter só no desenho: muitos jogadores têm o mesmo PDL.
        "scatter": [[int(v + rng.normal(0, 8)), _r(sc, 2)] for v, sc in zip(pts.value_solo, pts.score_shrunk)],
    }


# 6 ----------------------------------------------------------------------------------------------

PROFILE = ["kda", "deaths_pm", "gold_pm_diff", "cs_diff15", "kp", "dmg_pm", "dmg_share",
           "vision_pm", "solo_kills", "obj_dmg_pm"]


def top_profile(m: pd.DataFrame) -> dict:
    d = m[m.queue_id == SOLO_ID]
    z = _role_z(d, PROFILE).assign(win=d.win.to_numpy(), score=d.score.to_numpy())
    p = z.groupby("puuid").agg({**{c: "mean" for c in PROFILE}, "win": "mean", "score": ["mean", "size"]})
    p.columns = PROFILE + ["win", "score", "n"]
    p = p[p.n >= MIN_GAMES]
    k = 10
    p["shrunk"] = (p.n * p.score + k * d.score.mean()) / (p.n + k)
    cut = p.shrunk.quantile(0.9)
    top, rest = p[p.shrunk >= cut], p[p.shrunk < cut]
    rows = [[c, _r(top[c].mean() - rest[c].mean())] for c in PROFILE]
    rows.sort(key=lambda r: -abs(r[1]))
    return {
        "players": int(len(p)), "top_n": int(len(top)), "cut": _r(cut, 2),
        "win_top": _r(100 * top.win.mean(), 1), "win_rest": _r(100 * rest.win.mean(), 1),
        "diff": rows,
    }


# 7 ----------------------------------------------------------------------------------------------

def champions(m: pd.DataFrame) -> dict:
    out = {}
    for role in ROLES:
        d = m[m.role == role]
        c = d.groupby("champion").agg(n=("win", "size"), win=("win", "mean"), score=("score", "mean"),
                                      kda=("kda", "median"))
        top = c.sort_values("n", ascending=False).head(5)
        out[role] = [{"champion": k, "n": int(r.n), "win": _r(100 * r.win, 1),
                      "score": _r(r.score, 2), "kda": _r(r.kda, 2)} for k, r in top.iterrows()]
    return out


# 8 ----------------------------------------------------------------------------------------------

def two_queues(m: pd.DataFrame, players: pd.DataFrame) -> dict:
    def paired(rows, col, min_n=5):
        pr = _paired(rows, col, min_n)
        diff = pr[FLEX_ID] - pr[SOLO_ID]
        return {"n": int(len(pr)), "solo": _r(pr[SOLO_ID].mean()), "flex": _r(pr[FLEX_ID].mean()),
                "diff": _r(diff.mean()), "p": float(f"{stats.wilcoxon(diff).pvalue:.2g}")}

    out = {"score": paired(m, "score"), "score_lane": paired(m, "score_lane"),
           "win": paired(m.assign(win=100 * m.win), "win")}
    out["roles"] = {r: paired(m[m.role == r], "score", 3) for r in ROLES}

    z = _role_z(m, PROFILE)
    out["metrics"] = sorted([[c, paired(z, c)["diff"]] for c in PROFILE], key=lambda r: -abs(r[1]))

    anchors = pd.read_sql("SELECT DISTINCT puuid, match_id FROM match_ids", connect())
    d = m[["match_id", "queue_id", "puuid"]].merge(anchors.assign(anchor=True), on=["puuid", "match_id"], how="left")
    others = d[d.anchor.isna()].assign(master=lambda x: x.puuid.map(players.value_solo) >= MASTER_FLOOR)
    lob = others.groupby(["match_id", "queue_id"]).master.sum().groupby("queue_id").mean()
    out["lobby_master"] = {"solo": _r(lob[SOLO_ID], 2), "flex": _r(lob[FLEX_ID], 2)}

    g = m.assign(group=premade_sizes(m))
    out["groups"] = {q: {"alone": _r(100 * (x.group == 1).mean(), 1), "duo": _r(100 * (x.group == 2).mean(), 1),
                         "three_plus": _r(100 * (x.group >= 3).mean(), 1)}
                     for q, x in (("solo", g[g.queue_id == SOLO_ID]), ("flex", g[g.queue_id == FLEX_ID]))}
    return out


def run() -> str:
    m = pd.read_parquet(DATA_DIR / "match_scores.parquet")
    players = load_players()
    con = connect()
    data = {
        "totals": {
            "rows": int(len(m)), "matches": int(m.match_id.nunique()),
            "players_in_matches": int(m.puuid.nunique()), "players_ranked": int(len(players)),
            "timelines": con.execute("SELECT COUNT(*) FROM timelines").fetchone()[0],
            "solo_matches": int(m.loc[m.queue_id == SOLO_ID, "match_id"].nunique()),
            "flex_matches": int(m.loc[m.queue_id == FLEX_ID, "match_id"].nunique()),
            "metrics_full": len(FULL), "metrics_lane": len(LANE),
        },
        "role_cs": {r: [_r(x.mean(), 2), _r(x.std(), 2)] for r, x in m.groupby("role").cs_pm},
        "model": model(m),
        "win_loss": win_loss(m),
        "example": example_match(m),
        "reliability": reliability(m),
        "elo": score_vs_elo(players),
        "top": top_profile(m),
        "champions": champions(m),
        "queues": two_queues(m, players),
        # Atuações ao acaso para o letreiro de fundo do vídeo (sem identificar jogadores).
        "ticker": [{"queue": "solo" if r.queue_id == SOLO_ID else "flex", "role": r.role,
                    "champion": r.champion, "k": int(r.kills), "d": int(r.deaths), "a": int(r.assists),
                    "score": _r(r.score, 1), "win": int(r.win)}
                   for r in m.dropna(subset=["score"]).sample(80, random_state=SEED).itertuples()],
    }
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    (EXPORT_DIR / "perf_data.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    t, wl, rel, elo, top, q = (data[k] for k in ("totals", "win_loss", "reliability", "elo", "top", "queues"))
    lines = ["# Desempenho de jogadores", "",
             f"{t['matches']} partidas, {t['rows']} linhas jogador-partida, {t['players_in_matches']} jogadores.", "",
             "## Modelo", "", "| rota | AUC completo | AUC rota | maiores pesos |", "|:--|--:|--:|:--|"]
    for role, x in data["model"].items():
        lines.append(f"| {role} | {x['auc']} | {x['auc_lane']} | "
                     + ", ".join(f"{k} {v:+.2f}" for k, v in x["weights"][:5]) + " |")
    lines += ["", "## Vitórias e derrotas", "",
              "| nota | mediana vitória | mediana derrota | derrotas com nota ≥5 | vitórias com nota <5 | MVP no time que perdeu |",
              "|:--|--:|--:|--:|--:|--:|"]
    for col in ("score", "score_lane"):
        x = wl[col]
        lines.append(f"| `{col}` | {x['median_win']} | {x['median_loss']} | {x['loss_above5']}% | "
                     f"{x['win_below5']}% | {x['mvp_on_loser']}% |")
    lines += ["", f"## Confiabilidade ({rel['players']} jogadores com ≥20 partidas de solo)", "",
              "Correlação entre a média de n partidas e a de outras n partidas do mesmo jogador "
              "(métricas brutas em z-score por rota).", "",
              "| partidas | " + " | ".join(f"`{c}`" for c in rel["curve"]) + " |",
              "|--:|" + "--:|" * len(rel["curve"])]
    for i, (n, _) in enumerate(rel["curve"]["score"]):
        lines.append(f"| {n} | " + " | ".join(str(v[i][1]) for v in rel["curve"].values()) + " |")
    lines += [f"| {n} (projeção Spearman-Brown) | {v} | | | |" for n, v in rel["projected"]]
    lines += ["", "**Com 10 partidas de cada lado:**", "", "| métrica | correlação |", "|:--|--:|"]
    lines += [f"| `{c}` | {v} |" for c, v in rel["at10"]]
    lines += ["", f"## Nota x elo na solo ({elo['players']} jogadores com ≥{MIN_GAMES} partidas)", "",
              f"Spearman com o elo: todos {elo['rho_all']} (p={elo['p_all']}); só Master+ "
              f"{elo['rho_apex']} (p={elo['p_apex']}, n={elo['apex_players']}).", "",
              "| elo | jogadores | mediana | 25%–75% |", "|:--|--:|--:|:--|"]
    lines += [f"| {x['tier']} | {x['n']} | {x['median']} | {x['q1']}–{x['q3']} |" for x in elo["tiers"]]
    lines += ["", f"## Top 10% ({top['top_n']} de {top['players']} jogadores, nota ≥ {top['cut']})", "",
              f"Vitórias: top {top['win_top']}% x resto {top['win_rest']}%.", "",
              "| métrica | top - resto (DP da rota) |", "|:--|--:|"]
    lines += [f"| `{c}` | {v:+.3f} |" for c, v in top["diff"]]
    lines += ["", "## Duas filas (mesmo jogador, flex - solo)", "",
              "| medida | jogadores | solo | flex | flex - solo | p |", "|:--|--:|--:|--:|--:|--:|"]
    for k in ("score", "score_lane", "win"):
        x = q[k]
        lines.append(f"| {k} | {x['n']} | {x['solo']} | {x['flex']} | {x['diff']:+.3f} | {x['p']} |")
    lines += ["", f"Master+ da solo por lobby: solo {q['lobby_master']['solo']}, flex {q['lobby_master']['flex']}.", ""]
    report = "\n".join(lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "perf.md").write_text(report, encoding="utf-8")
    return report
