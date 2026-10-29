# Fontes do financas-ptbr

Matéria-prima dos termos de ações e FIIs do pack `financas-ptbr`. A engine não baixa esta pasta: ela baixa só o `pack.yaml` indicado no `index.json`.

## Regra

O pack é gerado a partir destes arquivos. Para corrigir um nome, corrija aqui e rode o gerador de novo. Não edite à mão a parte gerada do `pack.yaml`, porque ela é sobrescrita na próxima geração. Os termos curados à mão (fora da parte gerada) continuam sendo editados no `pack.yaml`.

## Arquivos

| Arquivo | Conteúdo | Linhas |
|---|---|---|
| `acoes.csv` | Ações e units | 675 |
| `fii.csv` | Fundos imobiliários | 648 |

## Colunas

- `ticker`: código de negociação.
- `nome`: nome como o ativo é falado ou conhecido.
- `apelidos`: outros nomes, inclusive antigos, separados por `;`.
- `tickers_antigos` (só em `acoes.csv`): códigos que a empresa já usou, separados por `;`.
- `classe` (ações) ou `tipo` (FII).
- `forma_falada` (só em `fii.csv`): ponto de partida para a pronúncia do ticker, por exemplo "MXRF onze". Não é a pronúncia confirmada.
- `palavra_comum` (só em `acoes.csv`): `sim` quando o nome também é palavra comum do português. Esses nomes só podem entrar no pack com contexto.
- `usar_no_pack`: `sim` ou `nao`.
- `status`:
  - `conferido`: nome conferido em fonte.
  - `revisado_manual`: nome revisado à mão, sem fonte registrada.
  - `nome_automatico`: nome gerado por script, sem revisão.
  - `verificar`: há uma dúvida, descrita em `nota`.
- `nota`: observações.
- `origem`: de onde veio a lista.

## Origem

A lista de tickers saiu do cadastro público de instrumentos da B3 de 20/10/2026. Os nomes foram limpos e revisados à mão. Das colunas do cadastro, só ficaram ticker, nome e classificação; razão social, nome de pregão, especificação e ISIN foram removidos. Fonte aberta para conferência: CVM Dados Abertos (FCA para ações e informe mensal para FIIs).
