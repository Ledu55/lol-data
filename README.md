# lol-data

Coleta e análise aberta de dados de League of Legends (Riot API, servidor BR). O código, os relatórios e um
dataset anonimizado estão aqui para que qualquer pessoa possa refazer as contas e **contestar as conclusões**.

## Estudo 1: os Master+ da flex são piores que os da solo?

Hipótese: jogadores Master+ da fila flex são menos habilidosos que os Master+ da solo/duo.
Coleta de 23 a 25/10/2026: 13.330 jogadores high elo das duas filas e 18.828 partidas (188 mil linhas jogador-partida).

**Veredito: confirmada em parte.** Cada conclusão abaixo aponta o relatório que a sustenta e o que poderia derrubá-la.

### 1. Um Master+ da flex é, em mediana, Diamante II na solo

[Teste A](reports/test_a.md): dos 3.782 Master+ da flex, só 32% são Master+ na solo e 25% estão abaixo de Diamante.

- **Ressalva:** o caminho inverso também cai, e cai mais. Master+ da solo são, em mediana, Esmeralda I na flex
  (queda de 582 pts contra 353). Elo cruzado mede habilidade, mas também dedicação a cada fila: Master+ da solo
  jogam pouca flex. Por isso o elo sozinho não basta, e os testes B e C medem desempenho dentro das partidas.

### 2. Na flex, o mesmo jogador enfrenta lobbies bem mais fracos e rende mais

[Estudos, §1](reports/studies.md): entre os outros 9 jogadores da partida, o mesmo jogador tem 5,7 Master+ da solo
na solo e 1,3 na flex (n=329). [Teste B](reports/test_bc.md): o `score_lane` dele é 0,24 maior na flex
(n=680, p=2,3e-6), e ele já está à frente do oponente de rota aos 10 e 15 minutos ([Estudos, §5](reports/studies.md)).

- **Ressalva:** na flex, 31% dos jogadores estão em grupos de 3+. Quando contamos só as partidas de flex em que o
  jogador estava sozinho ([Estudos, §4](reports/studies.md)), a diferença no score some (n=178, p=0,93), mas a
  vantagem de ouro e CS aos 15 min continua. Os grupos são inferidos, porque a API não os informa.

### 3. Na solo, os Master+ só da flex rendem o esperado para o próprio elo, ou um pouco mais

[Teste C](reports/test_bc.md): nas partidas de solo, o score mediano dos Master+ só da flex (4,99, n=480) e dos
Master+ da solo (5,06, n=5.316) não difere (p=0,21). Controlando pelo elo solo, o efeito é até positivo (+0,07, p=0,035).

- **Ressalva:** os dois grupos quase não se sobrepõem em elo solo, então esse controle é uma extrapolação.

### Limitações conhecidas

- O `score` completo carrega parte do resultado do time (AUC 0,93–0,96 para prever vitória, [modelo](reports/score_model.md)).
  O `score_lane`, que usa só métricas contra o oponente direto, reduz esse vazamento, sem eliminá-lo.
- Amostra de uma única foto de elo, de um servidor (BR), coletada com chave de desenvolvimento: 500 jogadores
  sorteados, mais 400 Master+ só da flex para reforçar o teste C.

## Como contestar

1. **Reproduza.** Baixe o [dataset público](DATASET.md) e rode as análises. Não é preciso chave da Riot, e os
   relatórios devem sair idênticos aos de `reports/`.
2. **Abra uma issue** com o formulário [Contestar uma conclusão](https://github.com/Ledu55/lol-data/issues/new?template=contestar-conclusao.yml):
   diga qual conclusão, o argumento e, se puder, a evidência (números ou código rodado sobre o dataset).
3. **Mande um PR** com o teste ou a correção. Veja [CONTRIBUTING.md](CONTRIBUTING.md).

Contestações que se sustentarem viram correções nos relatórios e entram no registro abaixo, com link para a issue.

### Registro de correções

Nenhuma até agora.

## Pipeline

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # cole sua RIOT_API_KEY (só para coletar)
```

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
| 10. Desempenho de jogadores (dados do vídeo "Quem carregou?") | `python -m lolflex perf` | 0 |
| 11. Dataset público anonimizado | `python -m lolflex export-public` | 0 |

Os passos 3, 7 e 9 também gravam `elo_flex_data.json` em `LOLFLEX_EXPORT`, com os mesmos números dos relatórios, sem
arredondar. É o que o vídeo "O elo da flex" lê.

Com o dataset público, rode a partir do passo 3, pulando 4, 5 e 8.
Todas as etapas de coleta são retomáveis (Ctrl+C e roda de novo). Os dados ficam em `data/lol.sqlite` e os relatórios em `reports/`.
Com a chave de desenvolvimento (100 req/2 min), o passo 2 leva de 2 a 3 horas e o passo 4 com 500 jogadores leva de 1 a 2 dias.

## Testes

- **A**: em que elo estão, na solo, os Master+ da flex? E o inverso? Compara a queda de elo ao trocar de fila (Mann-Whitney + IC por bootstrap).
- **B**: o mesmo jogador tem score diferente na solo e na flex? (Wilcoxon pareado)
- **C**: nas partidas de solo, quem é Master+ só na flex tem score menor que os Master+ da solo? Inclui OLS controlando pelo elo solo.

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

`plates` (`challenges.turretPlatesTaken`) conta as placas de torre pelas quais o jogador recebeu ouro, não só as
que ele destruiu: o ouro da placa é dividido com os aliados próximos. Nos patches 16.x as torres externa, interna e
do inibidor têm 5 placas cada, então um time pode tomar até 45; nas timelines, a soma do time fica em ~1,3× as
placas destruídas (`TURRET_PLATE_DESTROYED`).

## Export para o repo de conteúdo

Os JSON que os vídeos leem (`perf_data.json`) são gravados em `LOLFLEX_EXPORT` (`.env`). Sem a variável, ficam em `data/`.

## Licença

Código sob [MIT](LICENSE). Relatórios e dataset sob [CC BY 4.0](LICENSE-DATA).

lol-data não é endossado pela Riot Games e não reflete as opiniões da Riot Games nem de ninguém oficialmente
envolvido na produção ou gestão das propriedades da Riot Games. Riot Games e todas as propriedades associadas são
marcas comerciais ou marcas registradas da Riot Games, Inc.
