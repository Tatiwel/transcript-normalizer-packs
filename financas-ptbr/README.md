# financas-ptbr

Brazilian Portuguese videos about the stock market: listed companies and their tickers, financial indicators, valuation concepts, the people and organizations of the field. Version 0.3.9, 70 terms. It needs transcript-normalizer 0.7.0 or later (`min_engine`); older versions get 0.3.7, kept in `0.3.7/pack.yaml`.

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

Against each video's gold file, with no learned layer, after D-048 (only what reaches `normalized.txt` is scored), with engine 0.7.0:

| video | rows in scope | hits | misses | false positives | aliases recognized | aliases wrongly substituted |
|---|---|---|---|---|---|---|
| R2Qgz8tFWVI | 167 | 145 | 22 | 13 | 8 | 0 |
| wxgFO_fyfXg | 222 | 211 | 11 | 8 | 37 | 0 |
| 4wCtn8BWR4o | 45 | 44 | 1 | 2 | 15 | 0 |
| 4tTmY8Buask | 119 | 108 | 11 | 4 | 38 | 0 |

0.3.8 gives OPEX back its variant `Ox`, only in a video where CAPEX appears (D-086): R2Qgz8tFWVI regains three rows (142 → 145 hits), with false positives unchanged. Out of the domain, forced past pack fit, 0.3.8 changes no text. On a 16-minute street prank video (BIrASod49XY, D-035) the one annotation is a recognition (`tir` → TIR) that leaves the text as it was; its `Ox` is the Northeastern `oxe`, and with no CAPEX in the video it is not even proposed. On a science video about prions (yJxxTf0IQC8, D-035), nothing is applied; the names that only sound like BR Partners (`proteínas`) are asked, never applied (D-060). Pack fit (D-054) finds 15 to 44 of its terms with confidence in the four videos, 1 in the prank and 0 in the science video, so the engine would not apply it there at all.

The numbers come from `uv run python scripts/measure.py` in the engine repository; the decision numbers (D-0xx) point into its `docs/DECISIONS.md`.

## Maintainers

See `MAINTAINERS`.

0.3.9 removes 32 variants that are an ordinary word or phrase, too short, or the same as another term (D-032): CEMIG (`esse amigo`, `me caiu`, `do 100`, `sem amig`, `SEMI`, `CIC`), CPF, `taa`, `arte`, `bit` and `EBA` (EBITDA), `B`, `bit` and `be` (bilhão), `rap` and `rápid` (RAP), `valo`, `TR`, `índia`, `End`, `Word`, `NSS`, `Lu`, `anel`, `deck`, `ESA`, `Roy` and `ROI` (ROE), `ROK`, `Rid`, `Portou` and `partner` (BR Partners). The terms and their aliases stay, and no conditional form takes their place: if one of these garbles comes back, it is added again from a later transcript, with a gold file. The unit rule "number + B/bit/bi/be" is unchanged.
