import argparse
import logging

from . import collect, features, score, studies, test_a, test_bc


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    ap = argparse.ArgumentParser(prog="python -m lolflex")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("leagues", help="coleta Master/GM/Challenger das duas filas")
    p = sub.add_parser("ranks", help="coleta o elo de cada jogador nas duas filas")
    p.add_argument("--refresh", action="store_true")
    p = sub.add_parser("matches", help="coleta partidas recentes de uma amostra")
    p.add_argument("--sample", type=int, default=500, help="nº de jogadores (0 = todos)")
    p.add_argument("--per-queue", type=int, default=20)
    p.add_argument("--since-days", type=int, default=120)
    p.add_argument("--timelines", action="store_true", help="também baixa timelines (2x requisições)")
    p.add_argument("--group", choices=sorted(collect.GROUPS), default="all",
                   help="flex-only: só partidas de solo dos Master+ só da flex")
    p = sub.add_parser("test-a", help="análise de elo cruzado")
    p.add_argument("--min-games", type=int, default=20)
    sub.add_parser("features", help="extrai métricas das partidas")
    sub.add_parser("score", help="treina o score e agrega por jogador")
    sub.add_parser("test-bc", help="testes B e C com o score")
    sub.add_parser("studies", help="estudos complementares (lobbies, grupos, conversão de elo...)")

    a = ap.parse_args()
    if a.cmd == "leagues":
        collect.collect_leagues()
    elif a.cmd == "ranks":
        collect.collect_ranks(a.refresh)
    elif a.cmd == "matches":
        collect.collect_matches(a.sample or None, a.per_queue, a.since_days, a.timelines, a.group)
    elif a.cmd == "test-a":
        print(test_a.run(a.min_games))
    elif a.cmd == "features":
        print(f"{len(features.build())} linhas")
    elif a.cmd == "score":
        print(f"{len(score.build())} jogador-fila com score")
    elif a.cmd == "test-bc":
        print(test_bc.run())
    elif a.cmd == "studies":
        print(studies.run())


if __name__ == "__main__":
    main()
