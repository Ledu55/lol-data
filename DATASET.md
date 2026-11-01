# Dataset público do lol-data

Os dados usados nas análises deste repositório, sem identificar jogadores nem partidas. Gerado por
`python -m lolflex export-public` e publicado nas [Releases](https://github.com/Ledu55/lol-data/releases) do repositório.

## Como usar

1. Baixe `lol-data-dataset-<data>.zip` na Release mais recente.
2. Extraia o conteúdo na pasta `data/` do repositório (ou aponte `LOLFLEX_DATA` para outra pasta).
3. Rode as análises. Nenhuma delas faz requisições à Riot:

```powershell
python -m lolflex test-a      # reports/test_a.md
python -m lolflex score       # refaz match_scores e player_scores a partir de features.parquet
python -m lolflex test-bc     # reports/test_bc.md
python -m lolflex studies     # reports/studies.md
python -m lolflex perf        # reports/perf.md
```

Os relatórios devem sair iguais aos versionados em `reports/`. Se não saírem, abra uma issue.

## O que tem

| Arquivo / tabela | Conteúdo |
|---|---|
| `lol.sqlite` → `apex` | Jogadores Master, GM e Challenger das duas filas no momento da coleta |
| `lol.sqlite` → `ranks`, `rank_history` | Elo de cada jogador nas duas filas (tier, divisão, PDL, vitórias, derrotas) |
| `lol.sqlite` → `rank_fetch`, `match_fetch` | Quando o elo e as partidas de cada jogador foram coletados |
| `lol.sqlite` → `match_ids` | Quais partidas foram coletadas a partir de qual jogador (o "âncora" da partida) |
| `lol.sqlite` → `matches`, `timelines` | Só os IDs das partidas e a fila; o campo `data` (JSON bruto da Riot) fica vazio |
| `features.parquet` | Uma linha por jogador e partida, com as métricas extraídas (saída de `features`) |
| `match_scores.parquet` | O mesmo, com o score de cada partida (saída de `score`) |
| `player_scores.parquet` | Score médio de cada jogador por fila (saída de `score`) |

## Anonimização

- PUUIDs viram `p00001`, `p00002`... e IDs de partida viram `m00001`, `m00002`... A numeração segue a ordem
  dos IDs originais, então ordenações, validação cruzada e amostras com semente dão os mesmos resultados.
- Não há Riot IDs, nomes de invocador, horários das partidas nem o JSON bruto da API.
- O passo `features` não pode ser refeito com este dataset, porque ele lê o JSON bruto. Para auditá-lo, leia
  [`lolflex/features.py`](https://github.com/Ledu55/lol-data/blob/main/lolflex/features.py) ou colete os seus próprios dados com a sua chave da Riot.
- Combinações raras de campeões, rotas e estatísticas podem, em tese, permitir achar uma partida em sites de
  histórico. Não tente reidentificar jogadores.

## Licença

[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/deed.pt-br): pode usar e republicar, citando "lol-data (github.com/Ledu55/lol-data)".

lol-data não é endossado pela Riot Games e não reflete as opiniões da Riot Games nem de ninguém oficialmente
envolvido na produção ou gestão das propriedades da Riot Games. Riot Games e todas as propriedades associadas são
marcas comerciais ou marcas registradas da Riot Games, Inc.
