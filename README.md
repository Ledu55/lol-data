# lol-flex-vs-solo

Hipótese: jogadores high elo (Master+) da fila flex são menos habilidosos que os da solo/duo (servidor BR).

## Setup

```powershell
cd E:\lol-flex-vs-solo
copy .env.example .env   # cole sua RIOT_API_KEY
.venv\Scripts\activate
```

## Pipeline

| Passo | Comando | Requisições (aprox.) |
|---|---|---|
| 1. Ligas Master+/GM/Chall das duas filas | `python -m lolflex leagues` | 6 |
| 2. Elo de cada jogador nas duas filas | `python -m lolflex ranks` | 1 por jogador (~5–8 mil) |
| 3. **Teste A** (elo cruzado) | `python -m lolflex test-a` | 0 |
| 4. Partidas de uma amostra | `python -m lolflex matches --sample 500 --per-queue 20 --timelines` | ~2 por jogador + 2 por partida |
| 5. Métricas por partida | `python -m lolflex features` | 0 |
| 6. Score (estilo OP Score) | `python -m lolflex score` | 0 |
| 7. **Testes B e C** | `python -m lolflex test-bc` | 0 |
| 8. Mais partidas de solo dos Master+ só da flex (reforça o C) | `python -m lolflex matches --group flex-only --sample 400 --per-queue 15 --timelines` | ~2 por partida |
| 9. **Estudos complementares** | `python -m lolflex studies` | 0 |

Todas as etapas de coleta são retomáveis (Ctrl+C e roda de novo). Os dados ficam em `data/lol.sqlite` e os relatórios em `reports/`.
Com a chave de desenvolvimento (100 req/2 min), o passo 2 leva de 2 a 3 horas e o passo 4 com 500 jogadores leva de 1 a 2 dias. Para escalar, peça uma Personal API Key.

## Testes

- **A**: em que elo estão, na solo, os Master+ da flex? E o inverso? Compara a queda de elo ao trocar de fila (Mann-Whitney + IC por bootstrap).
- **B**: o mesmo jogador tem score diferente na solo e na flex? (Wilcoxon pareado)
- **C**: nas partidas de solo, quem é Master+ só na flex tem score menor que os Master+ da solo? Inclui OLS controlando pelo elo solo.
  Limitação: os dois grupos quase não se sobrepõem em elo solo, então esse controle é uma extrapolação.

## Estudos complementares (`reports/studies.md`)

1. Nível dos lobbies: quantos Master+ da solo há entre os outros 9 jogadores de cada partida.
2. Tabela de conversão: elo na solo de quem é Master+ na flex, por faixa de PDL (e o inverso).
3. Taxa de vitória do mesmo jogador nas duas filas.
4. Grupos pré-formados inferidos (≥3 partidas juntos no mesmo time) e o teste B sem eles.
5. Teste B sem o resultado do time: diferenças de ouro/XP/CS aos 10 e 15 min e score treinado só na solo.
6. Quais métricas e rotas explicam o teste B.
7. Qualidade do pareamento: dispersão de elo, atropelos, duração, rendições.
8. Campeões e rotas: rota principal, campeões mais jogados e o teste B só na rota principal.
10. Evolução do elo: cada `ranks` grava uma foto em `rank_history`; com duas fotos separadas por ≥14 dias, o relatório compara a variação de elo por grupo.

## Score

Os z-scores por rota alimentam uma regressão logística de vitória por rota. O score da partida é 10 × P(vitória), calculado fora da amostra.
O score do jogador é a média com shrinkage (k=10). `score_lane` usa só métricas contra o oponente de rota (exige `--timelines`), que dependem menos do resultado do time.
