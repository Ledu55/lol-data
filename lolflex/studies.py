"""Estudos complementares aos testes A, B e C.

1. Nível dos lobbies       5. Score sem o resultado do time
2. Tabela de conversão     6. Decomposição do teste B
3. Taxa de vitória         7. Qualidade do pareamento
4. Grupos pré-formados     8. Campeões e rotas
10. Evolução do elo entre coletas (precisa de duas coletas de elo)

Convenção: diferenças são sempre flex - solo (positivo = melhor na flex).
"""
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config, video_export
from .config import DATA_DIR, REPORTS_DIR
from .db import connect
from .ranks import MASTER_FLOOR, load_players, rank_value
from .score import FULL, LANE

SOLO_ID = config.QUEUE_IDS[config.SOLO]
FLEX_ID = config.QUEUE_IDS[config.FLEX]
MIN_MATCHES = 5
MIN_SHARED = 3  # partidas juntos no mesmo time para considerar dois jogadores um grupo
TIER_PT = ["Ferro", "Bronze", "Prata", "Ouro", "Platina", "Esmeralda", "Diamante"]
DIVS = ["IV", "III", "II", "I"]


def rank_label(v: float) -> str:
    if pd.isna(v):
        return "-"
    if v >= MASTER_FLOOR:
        return f"Master+ {v - MASTER_FLOOR:.0f} PDL"
    return f"{TIER_PT[int(v // 400)]} {DIVS[int(v % 400 // 100)]} {v % 100:.0f} PDL"


def _p(p: float) -> str:
    return f"{p:.2g}"


def _paired(rows: pd.DataFrame, col: str, min_n: int = MIN_MATCHES) -> pd.DataFrame:
    """Média por jogador em cada fila, só para quem tem min_n partidas nas duas."""
    g = rows.dropna(subset=[col]).groupby(["puuid", "queue_id"])[col].agg(["mean", "count"])
    g = g[g["count"] >= min_n]["mean"].unstack()
    return g.reindex(columns=[SOLO_ID, FLEX_ID]).dropna()


def _paired_row(name: str, paired: pd.DataFrame, digits: int = 3) -> str:
    if len(paired) < 10:
        return f"| {name} | {len(paired)} | - | - | - | - |"
    diff = paired[FLEX_ID] - paired[SOLO_ID]
    p = stats.wilcoxon(diff).pvalue
    return (f"| {name} | {len(paired)} | {paired[SOLO_ID].mean():.{digits}f} | "
            f"{paired[FLEX_ID].mean():.{digits}f} | {diff.mean():+.{digits}f} | {_p(p)} |")


def _paired_stats(paired: pd.DataFrame) -> dict | None:
    """Os mesmos números de _paired_row, sem arredondar, para o JSON do vídeo."""
    if len(paired) < 10:
        return None
    diff = paired[FLEX_ID] - paired[SOLO_ID]
    return {"jogadores": len(paired), "solo": paired[SOLO_ID].mean(), "flex": paired[FLEX_ID].mean(),
            "flex_menos_solo": diff.mean(), "p": stats.wilcoxon(diff).pvalue}


PAIRED_HEADER = ["| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |",
                 "|:--|--:|--:|--:|--:|--:|"]


def _role_z(rows: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """z-score por rota com as duas filas juntas (mesma régua do score)."""
    out = rows[["puuid", "queue_id", "match_id", "role"]].copy()
    for c in cols:
        g = rows.groupby("role")[c]
        out[c] = (rows[c] - g.transform("mean")) / g.transform("std")
    return out


# 1 ----------------------------------------------------------------------------------------------

def lobby_level(m: pd.DataFrame, players: pd.DataFrame, anchors: pd.DataFrame, out: dict) -> list[str]:
    d = m[["match_id", "queue_id", "puuid"]].copy()
    # Exclui o jogador da amostra (âncora) para olhar só os outros 9 da partida.
    d = d.merge(anchors.assign(anchor=True), on=["puuid", "match_id"], how="left")
    others = d[d.anchor.isna()].copy()
    others["high_elo"] = others.puuid.isin(players.index)
    others["master_solo"] = others.puuid.map(players.value_solo) >= MASTER_FLOOR
    others["elo_solo"] = others.puuid.map(players.value_solo)
    per_match = others.groupby(["match_id", "queue_id"]).agg(
        high_elo=("high_elo", "sum"), master_solo=("master_solo", "sum"),
        elo_solo=("elo_solo", "mean")).reset_index()

    lines = ["## 1. Nível dos lobbies", "",
             "Os outros 9 jogadores de cada partida (sem o jogador da amostra). "
             "Quem não está na lista high elo não é Master+ em nenhuma fila, então a contagem "
             "de Master+ da solo é exata.", "",
             "| fila | partidas | Master+ da solo por lobby (média) | high elo por lobby (média) | "
             "elo solo médio dos conhecidos |", "|:--|--:|--:|--:|--:|"]
    out["lobbies"] = {}
    for q, name in ((SOLO_ID, "solo"), (FLEX_ID, "flex")):
        x = per_match[per_match.queue_id == q]
        lines.append(f"| {name} | {len(x)} | {x.master_solo.mean():.2f} | {x.high_elo.mean():.2f} | "
                     f"{rank_label(x.elo_solo.mean())} |")
        out["lobbies"][name] = {"partidas": len(x), "master_solo": x.master_solo.mean(), "high_elo": x.high_elo.mean()}
    a = per_match.loc[per_match.queue_id == FLEX_ID, "master_solo"]
    b = per_match.loc[per_match.queue_id == SOLO_ID, "master_solo"]
    lines += ["", f"Mann-Whitney (flex < solo em Master+ por lobby): p={_p(stats.mannwhitneyu(a, b, alternative='less').pvalue)}.", ""]

    # Pareado pelo jogador da amostra: o mesmo jogador encontra lobbies mais fracos na flex?
    by_anchor = d[d.anchor.isna()].merge(anchors, on="match_id", suffixes=("", "_anchor"))
    by_anchor["master_solo"] = by_anchor.puuid.map(players.value_solo) >= MASTER_FLOOR
    lob = (by_anchor.groupby(["puuid_anchor", "match_id", "queue_id"]).master_solo.sum()
           .reset_index().rename(columns={"puuid_anchor": "puuid"}))
    pr = _paired(lob, "master_solo")
    lines += PAIRED_HEADER + [_paired_row("Master+ da solo nos outros 9 (mesmo jogador da amostra)", pr, 2), ""]
    out["lobbies"]["mesmo_jogador"] = _paired_stats(pr)
    return lines


# 2 ----------------------------------------------------------------------------------------------

def conversion_table(players: pd.DataFrame, out: dict, min_games: int = 20) -> list[str]:
    both = players[(players.games_solo >= min_games) & (players.games_flex >= min_games)]
    bins = [(0, 100), (100, 200), (200, 400), (400, 700), (700, 10_000)]
    lines = ["## 2. Tabela de conversão de elo", "",
             f"Jogadores com ≥{min_games} partidas nas duas filas. Só vale a partir de Master na fila "
             "de origem: abaixo disso a amostra só tem quem é Master+ na outra fila (truncada).", ""]
    out["conversao"] = {}
    for src, dst, title in (("flex", "solo", "Master+ na flex → elo na solo"),
                            ("solo", "flex", "Master+ na solo → elo na flex")):
        faixas = out["conversao"][f"{src}_para_{dst}"] = []
        lines += [f"**{title}**", "",
                  f"| PDL na {src} | jogadores | mediana na {dst} | faixa central (25%–75%) | % Master+ na {dst} |",
                  "|:--|--:|:--|:--|--:|"]
        for lo, hi in bins:
            v = both[f"value_{src}"] - MASTER_FLOOR
            x = both.loc[(v >= lo) & (v < hi), f"value_{dst}"]
            if len(x) < 10:
                continue
            label = f"{lo}+" if hi == 10_000 else f"{lo}–{hi - 1}"
            q1, med, q3 = x.quantile([0.25, 0.5, 0.75])
            lines.append(f"| {label} | {len(x)} | {rank_label(med)} | {rank_label(q1)} a {rank_label(q3)} | "
                         f"{100 * (x >= MASTER_FLOOR).mean():.0f}% |")
            faixas.append({"pdl_de": lo, "pdl_ate": None if hi == 10_000 else hi - 1, "jogadores": len(x),
                           "mediana": med, "mediana_rotulo": rank_label(med), "q1_rotulo": rank_label(q1),
                           "q3_rotulo": rank_label(q3), "pct_master": 100 * (x >= MASTER_FLOOR).mean()})
        lines.append("")
    return lines


# 3 ----------------------------------------------------------------------------------------------

def win_rates(m: pd.DataFrame, players: pd.DataFrame, out: dict, min_games: int = 20) -> list[str]:
    con = connect()
    r = pd.read_sql("SELECT puuid, queue, wins, losses FROM ranks", con)
    r["wr"] = r.wins / (r.wins + r.losses)
    r = r[(r.wins + r.losses) >= min_games]
    wide = r.pivot(index="puuid", columns="queue", values="wr").dropna()
    wide = wide.join(players[["apex_solo", "apex_flex"]])
    groups = [("Master+ só na solo", wide.apex_solo & ~wide.apex_flex),
              ("Master+ só na flex", wide.apex_flex & ~wide.apex_solo),
              ("Master+ nas duas", wide.apex_solo & wide.apex_flex)]
    lines = ["## 3. Taxa de vitória do mesmo jogador", "",
             f"**Temporada** (tabela de elo, ≥{min_games} partidas em cada fila). Estar no Master+ "
             "de uma fila exige ganhar nela, então os grupos \"só\" são enviesados a favor da própria "
             "fila; o grupo \"nas duas\" é o mais justo.", "",
             "| grupo | jogadores | % vitórias solo | % vitórias flex | flex - solo (p.p.) | p (Wilcoxon) |",
             "|:--|--:|--:|--:|--:|--:|"]
    out["vitorias"] = {}
    for (name, mask), key in zip(groups, ("so_solo", "so_flex", "nas_duas")):
        x = wide[mask]
        diff = x[config.FLEX] - x[config.SOLO]
        lines.append(f"| {name} | {len(x)} | {100 * x[config.SOLO].mean():.1f} | {100 * x[config.FLEX].mean():.1f} | "
                     f"{100 * diff.mean():+.1f} | {_p(stats.wilcoxon(diff).pvalue)} |")
        out["vitorias"][key] = {"jogadores": len(x), "solo": 100 * x[config.SOLO].mean(), "flex": 100 * x[config.FLEX].mean(),
                                "flex_menos_solo": 100 * diff.mean(), "p": stats.wilcoxon(diff).pvalue}
    pr = _paired(m.assign(win=100 * m.win), "win")
    lines += ["", "**Partidas da amostra** (≥5 em cada fila):", ""] + PAIRED_HEADER
    lines += [_paired_row("% vitórias", pr, 1), ""]
    out["vitorias"]["amostra"] = _paired_stats(pr)
    return lines


# 4 ----------------------------------------------------------------------------------------------

def premade_sizes(m: pd.DataFrame) -> pd.Series:
    """Tamanho estimado do grupo de cada jogador em cada partida (1 = sozinho)."""
    t = m[["match_id", "team_id", "puuid"]]
    pairs = t.merge(t, on=["match_id", "team_id"])
    pairs = pairs[pairs.puuid_x < pairs.puuid_y]
    shared = pairs.groupby(["puuid_x", "puuid_y"]).match_id.transform("nunique")
    linked = pairs[shared >= MIN_SHARED]

    size = {}
    for (match_id, _), g in linked.groupby(["match_id", "team_id"]):
        parent = {}

        def find(a):
            parent.setdefault(a, a)
            while parent[a] != a:
                a = parent[a]
            return a

        for a, b in zip(g.puuid_x, g.puuid_y):
            parent[find(a)] = find(b)
        roots = pd.Series({p: find(p) for p in parent})
        counts = roots.map(roots.value_counts())
        for p, n in counts.items():
            size[(match_id, p)] = n
    idx = pd.MultiIndex.from_frame(m[["match_id", "puuid"]])
    return pd.Series([size.get(k, 1) for k in idx], index=m.index)


def premades(m: pd.DataFrame, out: dict) -> list[str]:
    m = m.assign(group=premade_sizes(m))
    g4 = out["grupos"] = {"filas": {}, "sozinho": {}, "grupo_vs_sozinho": {}}
    lines = ["## 4. Grupos pré-formados", "",
             f"A API não informa grupos; aqui, dois jogadores do mesmo time que jogaram juntos em "
             f"≥{MIN_SHARED} partidas da amostra contam como grupo. Na solo o máximo legítimo é 2 "
             "(duo), então grupos maiores na solo medem o erro do método.", "",
             "| fila | sozinho | grupo de 2 | grupo de 3+ |", "|:--|--:|--:|--:|"]
    for q, name in ((SOLO_ID, "solo"), (FLEX_ID, "flex")):
        g = m.loc[m.queue_id == q, "group"]
        lines.append(f"| {name} | {100 * (g == 1).mean():.1f}% | {100 * (g == 2).mean():.1f}% | "
                     f"{100 * (g >= 3).mean():.1f}% |")
        g4["filas"][name] = {"sozinho": 100 * (g == 1).mean(), "grupo_2": 100 * (g == 2).mean(), "grupo_3_mais": 100 * (g >= 3).mean()}
    flex = m[m.queue_id == FLEX_ID]
    lines += ["", "**Teste B sem grupos**: flex só com partidas em que o jogador estava sozinho.", ""]
    lines += PAIRED_HEADER
    alone = pd.concat([m[m.queue_id == SOLO_ID], flex[flex.group == 1]])
    lane_z = _role_z(m, ["gold_diff15", "cs_diff15"]).assign(group=m.group)
    lane_alone = lane_z[(lane_z.queue_id == SOLO_ID) | (lane_z.group == 1)]
    for col in ("score", "score_lane"):
        pr = _paired(alone, col)
        lines.append(_paired_row(f"`{col}`, flex sozinho", pr))
        # Controle: os mesmos jogadores com todas as partidas de flex. Se o efeito também some
        # aqui, a diferença vem de quem são esses jogadores, não de jogar em grupo.
        same = m[m.puuid.isin(pr.index)]
        pr_same = _paired(same, col)
        lines.append(_paired_row(f"`{col}`, flex todas (mesmos jogadores)", pr_same))
        g4["sozinho"][col] = _paired_stats(pr)
        g4["sozinho"][f"{col}_todas"] = _paired_stats(pr_same)
    for col in ("gold_diff15", "cs_diff15"):
        pr = _paired(lane_alone, col)
        lines.append(_paired_row(f"`{col}` (DP), flex sozinho", pr))
        g4["sozinho"][col] = _paired_stats(pr)
    lines += ["", "**Na flex, o mesmo jogador rende mais em grupo?** (≥3 partidas de cada tipo)", "",
              "| medida | jogadores | sozinho | em grupo | grupo - sozinho | p (Wilcoxon) |",
              "|:--|--:|--:|--:|--:|--:|"]
    for col in ("score", "score_lane", "win"):
        x = flex.assign(kind=np.where(flex.group > 1, "grupo", "sozinho"))
        g = x.groupby(["puuid", "kind"])[col].agg(["mean", "count"])
        g = g[g["count"] >= 3]["mean"].unstack().reindex(columns=["sozinho", "grupo"]).dropna()
        if len(g) >= 10:
            diff = g.grupo - g.sozinho
            lines.append(f"| `{col}` | {len(g)} | {g.sozinho.mean():.3f} | {g.grupo.mean():.3f} | "
                         f"{diff.mean():+.3f} | {_p(stats.wilcoxon(diff).pvalue)} |")
            g4["grupo_vs_sozinho"][col] = {"jogadores": len(g), "sozinho": g.sozinho.mean(), "grupo": g.grupo.mean(),
                                           "grupo_menos_sozinho": diff.mean(), "p": stats.wilcoxon(diff).pvalue}
    return lines + [""]


# 5 ----------------------------------------------------------------------------------------------

def _solo_trained_score(m: pd.DataFrame) -> pd.Series:
    """Score treinado só na solo: fora da amostra na solo (GroupKFold) e aplicado direto na flex."""
    out = pd.Series(np.nan, index=m.index)
    for _, d in m.groupby("role"):
        cols = [c for c in FULL if d[c].notna().mean() > 0.8]
        X = d[cols].astype(float).fillna(d[cols].median())
        solo = (d.queue_id == SOLO_ID).to_numpy()
        Xs, ys = X[solo], d.win.to_numpy()[solo]

        def model():
            return make_pipeline(StandardScaler(), LogisticRegression(C=0.5, max_iter=2000))

        oof = np.zeros(len(Xs))
        for tr, te in GroupKFold(n_splits=5).split(Xs, ys, groups=d.match_id[solo]):
            oof[te] = model().fit(Xs.iloc[tr], ys[tr]).predict_proba(Xs.iloc[te])[:, 1]
        out.loc[Xs.index] = 10 * oof
        out.loc[X[~solo].index] = 10 * model().fit(Xs, ys).predict_proba(X[~solo])[:, 1]
    return out


def result_free(m: pd.DataFrame, out: dict) -> list[str]:
    lane = ["gold_diff10", "xp_diff10", "cs_diff10", "gold_diff15", "xp_diff15", "cs_diff15"]
    z = _role_z(m, lane)
    lines = ["## 5. Score sem o resultado do time", "",
             "Diferenças contra o oponente direto aos 10 e 15 minutos, sem modelo nenhum "
             "(z-score por rota; antes de o jogo se decidir), e um score treinado só com partidas de solo.", ""]
    lines += PAIRED_HEADER
    g5 = out["rota"] = {}
    for c in lane:
        pr = _paired(z, c)
        lines.append(_paired_row(f"`{c}` (desvios-padrão)", pr))
        g5[c] = _paired_stats(pr)
    pr = _paired(m.assign(s=_solo_trained_score(m)), "s")
    lines.append(_paired_row("score treinado só na solo", pr))
    g5["score_treinado_solo"] = _paired_stats(pr)
    return lines + [""]


# 6 ----------------------------------------------------------------------------------------------

def decompose(m: pd.DataFrame, out: dict) -> list[str]:
    cols = list(dict.fromkeys(FULL + LANE))
    z = _role_z(m, cols)
    rows = []
    for c in cols:
        pr = _paired(z, c)
        if len(pr) >= 10:
            diff = pr[FLEX_ID] - pr[SOLO_ID]
            rows.append((c, len(pr), diff.mean(), stats.wilcoxon(diff).pvalue))
    rows.sort(key=lambda r: -abs(r[2]))
    lines = ["## 6. O que explica o teste B", "",
             "Diferença flex - solo, em desvios-padrão da rota, das métricas do mesmo jogador "
             "(ordenado pelo tamanho do efeito).", "",
             "| métrica | jogadores | flex - solo (DP) | p (Wilcoxon) |", "|:--|--:|--:|--:|"]
    lines += [f"| `{c}` | {n} | {d:+.3f} | {_p(p)} |" for c, n, d, p in rows]
    lines += ["", "**Teste B por rota** (mesmo jogador, mesma rota, ≥3 partidas em cada fila):", "",
              "| rota | jogadores | score solo | score flex | flex - solo | p (Wilcoxon) |",
              "|:--|--:|--:|--:|--:|--:|"]
    out["metricas"] = [{"metrica": c, "jogadores": n, "flex_menos_solo_dp": d, "p": p} for c, n, d, p in rows]
    out["por_rota"] = {}
    for role, d in m.groupby("role"):
        pr = _paired(d, "score", 3)
        lines.append(_paired_row(role, pr))
        out["por_rota"][role] = _paired_stats(pr)
    return lines + [""]


# 7 ----------------------------------------------------------------------------------------------

def matchmaking(m: pd.DataFrame, players: pd.DataFrame, out: dict) -> list[str]:
    d = m.assign(elo=m.puuid.map(players.value_solo))
    team = d.groupby(["match_id", "queue_id", "team_id"]).agg(
        elo=("elo", "mean"), known=("elo", "count"), win=("win", "first"),
        gold15=("gold_diff15", lambda s: s.sum(min_count=5))).reset_index()
    match = d.groupby(["match_id", "queue_id"]).agg(
        spread=("elo", "std"), known=("elo", "count"),
        duration=("duration_min", "first"), surrender=("surrender", "max")).reset_index()
    first = team.groupby("match_id").first()
    match = match.join(first[["gold15"]], on="match_id")
    match["stomp"] = match.gold15.abs()

    lines = ["## 7. Qualidade do pareamento", "",
             "| fila | partidas | dispersão do elo solo (DP, ≥6 conhecidos) | diferença absoluta de ouro entre times aos 15 (mediana) | "
             "duração (mediana, min) | % terminadas em rendição |", "|:--|--:|--:|--:|--:|--:|"]
    g7 = out["pareamento"] = {}
    for q, name in ((SOLO_ID, "solo"), (FLEX_ID, "flex")):
        x = match[match.queue_id == q]
        lines.append(f"| {name} | {len(x)} | {x.loc[x.known >= 6, 'spread'].median():.0f} pts | "
                     f"{x.stomp.median():.0f} | {x.duration.median():.1f} | {100 * x.surrender.mean():.1f}% |")
        g7[name] = {"partidas": len(x), "dispersao_elo": x.loc[x.known >= 6, "spread"].median(),
                    "diferenca_ouro15": x.stomp.median(), "duracao_min": x.duration.median(),
                    "pct_rendicao": 100 * x.surrender.mean()}
    a, b = (match[match.queue_id == q] for q in (FLEX_ID, SOLO_ID))
    lines += ["", "Mann-Whitney flex vs solo: "
              f"dispersão p={_p(stats.mannwhitneyu(a.loc[a.known >= 6, 'spread'], b.loc[b.known >= 6, 'spread']).pvalue)}, "
              f"ouro aos 15 p={_p(stats.mannwhitneyu(a.stomp.dropna(), b.stomp.dropna()).pvalue)}, "
              f"duração p={_p(stats.mannwhitneyu(a.duration, b.duration).pvalue)}.", ""]

    # O time de elo maior ganha mais? E a dispersão prevê atropelos?
    gap = team[team.known >= 3].pivot_table(index=["match_id", "queue_id"], columns="team_id",
                                            values=["elo", "win"]).dropna()
    gap.columns = [f"{a}_{b}" for a, b in gap.columns]
    gap = gap.reset_index()
    gap["diff"] = gap.elo_100 - gap.elo_200
    gap = gap[gap["diff"].abs() >= 100]
    gap["fav_won"] = np.where(gap["diff"] > 0, gap.win_100, 1 - gap.win_100)
    lines += ["| fila | partidas com diferença ≥100 pts entre times | % vitórias do time de elo maior | "
              "correlação dispersão × ouro aos 15 (Spearman) |", "|:--|--:|--:|--:|"]
    for q, name in ((SOLO_ID, "solo"), (FLEX_ID, "flex")):
        g = gap[gap.queue_id == q]
        x = match[(match.queue_id == q) & (match.known >= 6)].dropna(subset=["stomp"])
        rho = stats.spearmanr(x.spread, x.stomp)
        lines.append(f"| {name} | {len(g)} | {100 * g.fav_won.mean():.1f}% | {rho.statistic:+.2f} (p={_p(rho.pvalue)}) |")
        g7[name].update({"partidas_com_favorito": len(g), "pct_favorito_vence": 100 * g.fav_won.mean()})
    return lines + [""]


# 8 ----------------------------------------------------------------------------------------------

def champions_roles(m: pd.DataFrame, out: dict) -> list[str]:
    def ranked(col):
        c = m.groupby(["puuid", col]).size().rename("n").reset_index()
        c = c.sort_values(["puuid", "n"], ascending=[True, False])
        return c.assign(rank=c.groupby("puuid").cumcount())

    roles, champs = ranked("role"), ranked("champion")
    main_role = roles[roles["rank"] == 0].set_index("puuid").role
    top3 = champs.loc[champs["rank"] < 3, ["puuid", "champion"]].assign(top3=100.0)
    x = m.merge(top3, on=["puuid", "champion"], how="left").fillna({"top3": 0.0})
    x["main_role"] = (x.role == x.puuid.map(main_role)).astype(float) * 100
    div = x.groupby(["puuid", "queue_id"]).champion.agg(["nunique", "size"])
    div = div[div["size"] >= MIN_MATCHES]
    div = (div["nunique"] / div["size"]).unstack().reindex(columns=[SOLO_ID, FLEX_ID]).dropna()

    lines = ["## 8. Campeões e rotas", "",
             "Rota principal e top 3 campeões de cada jogador contam as duas filas juntas.", ""]
    main, top = _paired(x, "main_role"), _paired(x, "top3")
    lines += PAIRED_HEADER
    lines += [_paired_row("% partidas na rota principal", main, 1),
              _paired_row("% partidas com campeão do top 3", top, 1),
              _paired_row("campeões diferentes por partida", div, 3)]
    g8 = out["campeoes_rotas"] = {"rota_principal": _paired_stats(main), "campeao_top3": _paired_stats(top),
                                  "campeoes_por_partida": _paired_stats(div)}
    on_role = x[x.main_role == 100]
    lines += ["", "**Teste B só na rota principal**:", ""] + PAIRED_HEADER
    for col in ("score", "score_lane"):
        pr = _paired(on_role, col)
        lines.append(_paired_row(f"`{col}`", pr))
        g8[f"{col}_rota_principal"] = _paired_stats(pr)
    return lines + [""]


# 10 ---------------------------------------------------------------------------------------------

def elo_trend(players: pd.DataFrame) -> list[str]:
    h = pd.read_sql("SELECT * FROM rank_history", connect())
    h["day"] = h.fetched_at.str[:10]
    lines = ["## 10. Evolução do elo entre coletas", ""]
    if h.day.nunique() < 2 or (pd.to_datetime(h.day.max()) - pd.to_datetime(h.day.min())).days < 14:
        return lines + ["Só há uma coleta de elo. Rode `python -m lolflex ranks --refresh` daqui a "
                        "algumas semanas e depois `python -m lolflex studies`.", ""]
    h["value"] = [rank_value(t, d, lp) for t, d, lp in zip(h.tier, h.division, h.lp)]
    h = h.sort_values("fetched_at")
    g = h.groupby(["puuid", "queue"])
    delta = (g.value.last() - g.value.first()).unstack()
    games = (g.wins.last() + g.losses.last() - g.wins.first() - g.losses.first()).unstack()
    delta = delta.join(players[["apex_solo", "apex_flex"]])
    lines += [f"Entre {h.day.min()} e {h.day.max()}.", "",
              "| grupo | jogadores | variação na solo (mediana, pts) | partidas novas na solo (mediana) |",
              "|:--|--:|--:|--:|"]
    for name, mask in (("Master+ só na solo", delta.apex_solo & ~delta.apex_flex),
                       ("Master+ só na flex", delta.apex_flex & ~delta.apex_solo),
                       ("Master+ nas duas", delta.apex_solo & delta.apex_flex)):
        x = delta.loc[mask, config.SOLO].dropna()
        lines.append(f"| {name} | {len(x)} | {x.median():+.0f} | "
                     f"{games.loc[x.index, config.SOLO].median():.0f} |")
    return lines + [""]


def run() -> str:
    m = pd.read_parquet(DATA_DIR / "match_scores.parquet")
    players = load_players()
    anchors = pd.read_sql("SELECT DISTINCT puuid, match_id FROM match_ids", connect())
    lines = ["# Estudos complementares", "",
             f"{m.match_id.nunique()} partidas, {len(m)} linhas jogador-partida. "
             "Diferenças são flex - solo (positivo = melhor na flex).", ""]
    dados = {"partidas": m.match_id.nunique(), "linhas": len(m)}
    lines += lobby_level(m, players, anchors, dados)
    lines += conversion_table(players, dados)
    lines += win_rates(m, players, dados)
    lines += premades(m, dados)
    lines += result_free(m, dados)
    lines += decompose(m, dados)
    lines += matchmaking(m, players, dados)
    lines += champions_roles(m, dados)
    lines += elo_trend(players)
    video_export.gravar("estudos", dados)
    report = "\n".join(lines)
    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "studies.md").write_text(report, encoding="utf-8")
    return report
