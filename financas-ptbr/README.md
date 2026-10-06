# financas-ptbr

Brazilian Portuguese videos about the stock market: listed companies and their tickers, financial indicators, valuation concepts, the people and organizations of the field. Version 0.3.4, 70 terms:

| class | terms | examples |
|---|---|---|
| indicador | 22 | EBITDA, dividend yield, preço teto, TIR |
| companhia | 17 | CEMIG, CPFL, Taesa, BR Partners |
| conceito | 12 | valuation, buy and hold, free float |
| pessoa | 6 | Warren Buffett, Décio Bazin |
| organizacao | 5 | ANEEL, Geração Dividendos |
| sigla | 4 | RAP, DEC, FEC, RI |
| unidade | 2 | bilhão, tri |
| ferramenta | 2 | Adapta Valuer, Ward |

## Where the terms came from

Four videos, each checked line by line against the tool's output. They are the regression fixtures of the engine repository (`fixtures/<id>/`), with a hand-checked gold file each.

| video | channel | published | subject |
|---|---|---|---|
| [R2Qgz8tFWVI](https://youtu.be/R2Qgz8tFWVI) | Geração Dividendos | 2026-08-21 | CEMIG falling: trap or opportunity |
| [wxgFO_fyfXg](https://youtu.be/wxgFO_fyfXg) | Geração Dividendos | 2026-08-25 | CMIG4 against CPFE3, electric utilities compared |
| [4wCtn8BWR4o](https://youtu.be/4wCtn8BWR4o) | Adan Paulo - Adapta Partners | 2026-09-18 | CEMIG's new dividend |
| [4tTmY8Buask](https://youtu.be/4tTmY8Buask) | Adan Paulo - Adapta Partners | 2026-09-27 | BRBI11, a new sector |

Version history is in the comment at the top of `pack.yaml`.

## How it measures

Against each video's gold file, with no learned layer, after D-048 (only what reaches `normalized.txt` is scored):

| video | rows in scope | hits | misses | false positives | aliases recognized | aliases wrongly substituted |
|---|---|---|---|---|---|---|
| R2Qgz8tFWVI | 167 | 142 | 25 | 16 | 8 | 0 |
| wxgFO_fyfXg | 222 | 211 | 11 | 10 | 37 | 0 |
| 4wCtn8BWR4o | 45 | 44 | 1 | 2 | 15 | 0 |
| 4tTmY8Buask | 119 | 108 | 11 | 4 | 38 | 0 |

Out of the domain, on a 16-minute street prank video (D-035), 0.3.4 applies nothing: the one annotation left is a recognition (`tir` → TIR) that changes no text. Pack fit (D-054) finds 15 to 44 of its terms with confidence in the four videos and 1 in the prank, so the engine would not apply it there at all.

The numbers come from `uv run python scripts/measure.py` in the engine repository; the decision numbers (D-0xx) point into its `docs/DECISIONS.md`.

## Maintainers

See `MAINTAINERS`.
