# Estudos complementares

18828 partidas, 188268 linhas jogador-partida. Diferenças são flex - solo (positivo = melhor na flex).

## 1. Nível dos lobbies

Os outros 9 jogadores de cada partida (sem o jogador da amostra). Quem não está na lista high elo não é Master+ em nenhuma fila, então a contagem de Master+ da solo é exata.

| fila | partidas | Master+ da solo por lobby (média) | high elo por lobby (média) | elo solo médio dos conhecidos |
|:--|--:|--:|--:|--:|
| solo | 12960 | 4.77 | 4.92 | Master+ 416 PDL |
| flex | 5868 | 1.36 | 2.67 | Master+ 55 PDL |

Mann-Whitney (flex < solo em Master+ por lobby): p=0.

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| Master+ da solo nos outros 9 (mesmo jogador da amostra) | 329 | 5.70 | 1.33 | -4.37 | 3.2e-49 |

## 2. Tabela de conversão de elo

Jogadores com ≥20 partidas nas duas filas. Só vale a partir de Master na fila de origem: abaixo disso a amostra só tem quem é Master+ na outra fila (truncada).

**Master+ na flex → elo na solo**

| PDL na flex | jogadores | mediana na solo | faixa central (25%–75%) | % Master+ na solo |
|:--|--:|:--|:--|--:|
| 0–99 | 1992 | Diamante III 60 PDL | Esmeralda I 75 PDL a Master+ 0 PDL | 26% |
| 100–199 | 407 | Diamante II 75 PDL | Diamante IV 15 PDL a Master+ 27 PDL | 30% |
| 200–399 | 395 | Diamante II 99 PDL | Diamante IV 36 PDL a Master+ 128 PDL | 37% |
| 400–699 | 352 | Diamante I 75 PDL | Diamante III 62 PDL a Master+ 234 PDL | 45% |
| 700+ | 354 | Master+ 136 PDL | Diamante I 14 PDL a Master+ 696 PDL | 65% |

**Master+ na solo → elo na flex**

| PDL na solo | jogadores | mediana na flex | faixa central (25%–75%) | % Master+ na flex |
|:--|--:|:--|:--|--:|
| 0–99 | 1890 | Diamante IV 49 PDL | Esmeralda II 14 PDL a Diamante I 37 PDL | 17% |
| 100–199 | 831 | Diamante IV 53 PDL | Esmeralda I 1 PDL a Diamante I 28 PDL | 18% |
| 200–399 | 1052 | Diamante III 16 PDL | Esmeralda I 2 PDL a Diamante I 75 PDL | 18% |
| 400–699 | 934 | Diamante III 62 PDL | Esmeralda I 58 PDL a Diamante I 75 PDL | 22% |
| 700+ | 1033 | Diamante II 75 PDL | Esmeralda I 87 PDL a Master+ 5 PDL | 28% |

## 3. Taxa de vitória do mesmo jogador

**Temporada** (tabela de elo, ≥20 partidas em cada fila). Estar no Master+ de uma fila exige ganhar nela, então os grupos "só" são enviesados a favor da própria fila; o grupo "nas duas" é o mais justo.

| grupo | jogadores | % vitórias solo | % vitórias flex | flex - solo (p.p.) | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| Master+ só na solo | 4576 | 52.6 | 54.6 | +2.0 | 6.4e-49 |
| Master+ só na flex | 2348 | 52.1 | 54.4 | +2.3 | 4.7e-83 |
| Master+ nas duas | 1152 | 52.9 | 55.2 | +2.3 | 1.7e-43 |

**Partidas da amostra** (≥5 em cada fila):

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| % vitórias | 680 | 51.8 | 54.5 | +2.6 | 0.00079 |

## 4. Grupos pré-formados

A API não informa grupos; aqui, dois jogadores do mesmo time que jogaram juntos em ≥3 partidas da amostra contam como grupo. Na solo o máximo legítimo é 2 (duo), então grupos maiores na solo medem o erro do método.

| fila | sozinho | grupo de 2 | grupo de 3+ |
|:--|--:|--:|--:|
| solo | 91.4% | 8.6% | 0.1% |
| flex | 58.7% | 10.6% | 30.6% |

**Teste B sem grupos**: flex só com partidas em que o jogador estava sozinho.

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| `score`, flex sozinho | 178 | 5.237 | 5.075 | -0.162 | 0.2 |
| `score`, flex todas (mesmos jogadores) | 178 | 5.237 | 5.165 | -0.072 | 0.47 |
| `score_lane`, flex sozinho | 178 | 5.202 | 5.210 | +0.008 | 0.93 |
| `score_lane`, flex todas (mesmos jogadores) | 178 | 5.202 | 5.279 | +0.077 | 0.41 |
| `gold_diff15` (DP), flex sozinho | 178 | 0.013 | 0.096 | +0.083 | 0.049 |
| `cs_diff15` (DP), flex sozinho | 178 | -0.022 | 0.109 | +0.132 | 0.0016 |

**Na flex, o mesmo jogador rende mais em grupo?** (≥3 partidas de cada tipo)

| medida | jogadores | sozinho | em grupo | grupo - sozinho | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| `score` | 352 | 4.999 | 5.118 | +0.120 | 0.42 |
| `score_lane` | 352 | 5.152 | 5.175 | +0.023 | 0.69 |
| `win` | 352 | 0.499 | 0.524 | +0.025 | 0.28 |

## 5. Score sem o resultado do time

Diferenças contra o oponente direto aos 10 e 15 minutos, sem modelo nenhum (z-score por rota; antes de o jogo se decidir), e um score treinado só com partidas de solo.

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| `gold_diff10` (desvios-padrão) | 680 | 0.011 | 0.188 | +0.178 | 1.3e-21 |
| `xp_diff10` (desvios-padrão) | 680 | 0.008 | 0.152 | +0.144 | 1.2e-14 |
| `cs_diff10` (desvios-padrão) | 680 | -0.029 | 0.168 | +0.197 | 8.1e-24 |
| `gold_diff15` (desvios-padrão) | 680 | 0.021 | 0.215 | +0.194 | 2.6e-23 |
| `xp_diff15` (desvios-padrão) | 680 | 0.021 | 0.173 | +0.153 | 5.7e-16 |
| `cs_diff15` (desvios-padrão) | 680 | -0.029 | 0.179 | +0.208 | 7.6e-27 |
| score treinado só na solo | 680 | 5.171 | 5.328 | +0.157 | 0.018 |

## 6. O que explica o teste B

Diferença flex - solo, em desvios-padrão da rota, das métricas do mesmo jogador (ordenado pelo tamanho do efeito).

| métrica | jogadores | flex - solo (DP) | p (Wilcoxon) |
|:--|--:|--:|--:|
| `dmg_pm` | 680 | +0.306 | 2.2e-33 |
| `dmg_share` | 680 | +0.282 | 8.6e-29 |
| `solo_kills` | 680 | +0.279 | 9.3e-28 |
| `max_cs_adv` | 680 | +0.254 | 1.3e-31 |
| `dmg_pm_diff` | 680 | +0.243 | 4.2e-29 |
| `cs_diff15` | 680 | +0.208 | 7.6e-27 |
| `cs_diff10` | 680 | +0.197 | 8.1e-24 |
| `gold_pm_diff` | 680 | +0.194 | 4e-21 |
| `gold_diff15` | 680 | +0.194 | 2.6e-23 |
| `kp` | 680 | +0.193 | 3.6e-21 |
| `cs_pm_diff` | 680 | +0.189 | 1.9e-21 |
| `gold_pm` | 680 | +0.183 | 1.4e-17 |
| `gold_diff10` | 680 | +0.178 | 1.3e-21 |
| `max_lvl_lead` | 680 | +0.171 | 1.9e-16 |
| `xp_diff15` | 680 | +0.153 | 5.7e-16 |
| `xp_diff10` | 680 | +0.144 | 1.2e-14 |
| `dmg_taken_share` | 680 | +0.141 | 3.6e-12 |
| `plates` | 680 | +0.065 | 0.00022 |
| `vision_pm_diff` | 680 | +0.057 | 0.00024 |
| `vision_adv` | 680 | +0.050 | 0.0015 |
| `deaths_pm` | 680 | +0.048 | 0.0085 |
| `obj_dmg_pm` | 680 | +0.043 | 0.0047 |
| `kda` | 680 | +0.038 | 0.067 |
| `cs10` | 680 | +0.033 | 0.017 |
| `cs_pm` | 680 | -0.024 | 0.28 |
| `vision_pm` | 680 | -0.016 | 0.42 |

**Teste B por rota** (mesmo jogador, mesma rota, ≥3 partidas em cada fila):

| rota | jogadores | score solo | score flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| BOTTOM | 207 | 5.101 | 5.585 | +0.484 | 0.0061 |
| JUNGLE | 198 | 5.126 | 5.395 | +0.269 | 0.26 |
| MIDDLE | 169 | 5.278 | 5.423 | +0.145 | 0.35 |
| TOP | 168 | 5.362 | 5.475 | +0.113 | 0.45 |
| UTILITY | 175 | 5.045 | 5.457 | +0.412 | 0.0097 |

## 7. Qualidade do pareamento

| fila | partidas | dispersão do elo solo (DP, ≥6 conhecidos) | diferença absoluta de ouro entre times aos 15 (mediana) | duração (mediana, min) | % terminadas em rendição |
|:--|--:|--:|--:|--:|--:|
| solo | 12960 | 282 pts | 2661 | 28.3 | 21.9% |
| flex | 5868 | 491 pts | 2621 | 29.8 | 24.5% |

Mann-Whitney flex vs solo: dispersão p=1.5e-287, ouro aos 15 p=0.28, duração p=3.8e-44.

| fila | partidas com diferença ≥100 pts entre times | % vitórias do time de elo maior | correlação dispersão × ouro aos 15 (Spearman) |
|:--|--:|--:|--:|
| solo | 4221 | 64.8% | +0.02 (p=0.18) |
| flex | 1005 | 54.5% | +0.02 (p=0.38) |

## 8. Campeões e rotas

Rota principal e top 3 campeões de cada jogador contam as duas filas juntas.

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| % partidas na rota principal | 680 | 70.6 | 58.3 | -12.3 | 3.1e-17 |
| % partidas com campeão do top 3 | 680 | 65.0 | 53.9 | -11.1 | 1.1e-21 |
| campeões diferentes por partida | 680 | 0.492 | 0.622 | +0.131 | 4.1e-33 |

**Teste B só na rota principal**:

| medida | jogadores | solo | flex | flex - solo | p (Wilcoxon) |
|:--|--:|--:|--:|--:|--:|
| `score` | 370 | 5.312 | 5.455 | +0.143 | 0.12 |
| `score_lane` | 370 | 5.268 | 5.519 | +0.251 | 0.00069 |

## 10. Evolução do elo entre coletas

Só há uma coleta de elo. Rode `python -m lolflex ranks --refresh` daqui a algumas semanas e depois `python -m lolflex studies`.
