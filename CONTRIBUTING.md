# Contribuindo

Contestações são bem-vindas. Elas são o motivo de este repositório ser aberto.

## Contestar uma conclusão

Use o formulário [Contestar uma conclusão](https://github.com/Ledu55/lol-data/issues/new?template=contestar-conclusao.yml). Uma boa contestação:

- diz qual conclusão e qual relatório, tabela ou linha de código ela ataca;
- traz evidência que outra pessoa consiga reproduzir, de preferência rodada sobre o [dataset público](DATASET.md),
  citando a versão (a data no nome do zip);
- propõe o teste que resolveria a dúvida.

"Não acredito" sem argumento não é contestação, mas "não entendi por que este teste responde a esta pergunta" é.

## Mandar código

1. Faça um fork e crie uma branch.
2. Se a mudança altera resultados, rode de novo as etapas afetadas e commite os relatórios em `reports/` junto com o código,
   para que o diff mostre o que mudou nos números.
3. Explique no PR o que mudou e por quê, e link a issue de contestação, se houver.

Mudanças de método (novo teste, outra métrica, outro corte de amostra) entram como etapa ou estudo novo, sem
apagar o resultado antigo, para que as duas versões possam ser comparadas.

## Dados

- Nunca commite `.env`, `data/` ou qualquer arquivo com PUUIDs, Riot IDs ou IDs de partida.
- Não tente reidentificar jogadores do dataset público.
- Quem coletar com a própria chave da Riot segue as [políticas de desenvolvedor da Riot](https://developer.riotgames.com/policies/general).
