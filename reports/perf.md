# Desempenho de jogadores

18828 partidas, 188268 linhas jogador-partida, 62560 jogadores.

## Modelo

| rota | AUC completo | AUC rota | maiores pesos |
|:--|--:|--:|:--|
| TOP | 0.93 | 0.811 | kda +2.84, gold_pm_diff +1.89, dmg_share -1.56, kp -1.17, dmg_pm +0.84 |
| JUNGLE | 0.959 | 0.854 | kda +3.17, gold_pm_diff +1.64, dmg_share -1.46, dmg_pm +1.11, kp -0.94 |
| MIDDLE | 0.934 | 0.834 | kda +3.14, dmg_share -1.36, gold_pm_diff +1.27, kp -1.03, dmg_pm +0.88 |
| BOTTOM | 0.957 | 0.867 | kda +3.26, gold_pm_diff +2.24, dmg_share -1.33, kp -1.21, obj_dmg_pm +0.94 |
| UTILITY | 0.954 | 0.861 | gold_pm_diff +2.62, kda +1.81, dmg_share -1.64, dmg_pm +1.36, kp -0.91 |

## Vitórias e derrotas

| nota | mediana vitória | mediana derrota | derrotas com nota ≥5 | vitórias com nota <5 | MVP no time que perdeu |
|:--|--:|--:|--:|--:|--:|
| `score` | 9.29 | 0.74 | 12.3% | 12.9% | 5.6% |
| `score_lane` | 7.29 | 2.45 | 20.9% | 25.2% | 10.5% |

## Confiabilidade (740 jogadores com ≥20 partidas de solo)

Correlação entre a média de n partidas e a de outras n partidas do mesmo jogador (métricas brutas em z-score por rota).

| partidas | `score` | `score_lane` | `kda` | `cs_pm` |
|--:|--:|--:|--:|--:|
| 1 | 0.021 | 0.021 | 0.054 | 0.185 |
| 2 | 0.008 | 0.035 | 0.08 | 0.31 |
| 3 | 0.034 | 0.058 | 0.136 | 0.405 |
| 5 | 0.05 | 0.096 | 0.198 | 0.523 |
| 7 | 0.052 | 0.112 | 0.253 | 0.61 |
| 10 | 0.079 | 0.153 | 0.326 | 0.692 |
| 20 (projeção Spearman-Brown) | 0.146 | | | |
| 30 (projeção Spearman-Brown) | 0.204 | | | |
| 50 (projeção Spearman-Brown) | 0.299 | | | |

**Com 10 partidas de cada lado:**

| métrica | correlação |
|:--|--:|
| `vision_pm` | 0.77 |
| `cs_pm` | 0.692 |
| `dmg_share` | 0.606 |
| `deaths_pm` | 0.605 |
| `solo_kills` | 0.476 |
| `cs_diff15` | 0.436 |
| `kda` | 0.326 |
| `kp` | 0.273 |
| `gold_diff15` | 0.271 |
| `score_lane` | 0.153 |
| `score` | 0.079 |
| `win` | 0.002 |

## Nota x elo na solo (2768 jogadores com ≥10 partidas)

Spearman com o elo: todos 0.059 (p=0.0019); só Master+ 0.083 (p=4.9e-05, n=2381).

| elo | jogadores | mediana | 25%–75% |
|:--|--:|--:|:--|
| Esmeralda | 93 | 4.96 | 4.59–5.41 |
| Diamante | 277 | 5.09 | 4.59–5.56 |
| Master | 2149 | 5.06 | 4.62–5.47 |
| Grão-Mestre | 172 | 5.02 | 4.61–5.56 |
| Desafiante | 60 | 5.24 | 4.74–5.67 |

## Top 10% (301 de 3002 jogadores, nota ≥ 5.88)

Vitórias: top 69.3% x resto 49.3%.

| métrica | top - resto (DP da rota) |
|:--|--:|
| `deaths_pm` | -0.415 |
| `gold_pm_diff` | +0.411 |
| `kda` | +0.409 |
| `obj_dmg_pm` | +0.400 |
| `cs_diff15` | +0.164 |
| `dmg_pm` | +0.104 |
| `solo_kills` | +0.082 |
| `vision_pm` | +0.065 |
| `kp` | +0.034 |
| `dmg_share` | -0.003 |

## Duas filas (mesmo jogador, flex - solo)

| medida | jogadores | solo | flex | flex - solo | p |
|:--|--:|--:|--:|--:|--:|
| score | 680 | 5.159 | 5.304 | +0.145 | 0.028 |
| score_lane | 680 | 5.141 | 5.382 | +0.242 | 2.3e-06 |
| win | 680 | 51.808 | 54.453 | +2.646 | 0.00079 |

Master+ da solo por lobby: solo 4.77, flex 1.36.
