# financas-ptbr

Brazilian Portuguese videos about the stock market: listed companies and their tickers, financial indicators, valuation concepts, the people and organizations of the field. Version 0.4.0, 352 terms: 70 curated by hand and 282 listed companies generated from `fontes/acoes.csv`. It needs transcript-normalizer 0.8.0 or later (`min_engine`), for `match: exact` (D-090). Engines 0.7.x get 0.3.9, kept in `0.3.9/pack.yaml`; older ones get 0.3.7, kept in `0.3.7/pack.yaml`.

| class | terms | examples |
|---|---|---|
| companhia | 299 | CEMIG, CPFL, Taesa, BR Partners; generated: Petrobras, Vale, Axia Energia |
| indicador | 22 | EBITDA, dividend yield, preço teto, TIR |
| conceito | 12 | valuation, buy and hold, free float |
| pessoa | 6 | Warren Buffett, Décio Bazin |
| organizacao | 5 | ANEEL, Guepardo |
| sigla | 4 | RAP, DEC, FEC, RI |
| unidade | 2 | bilhão, tri |
| ferramenta | 2 | Ward |

## Where the terms came from

Four videos in Portuguese about stocks listed on B3, each checked line by line against the tool's output. They are the regression fixtures of the engine repository, each with a hand-checked gold file. Below they are videos 1 to 4.

Version history is in the comment at the top of `pack.yaml`.

## The generated companies

From 0.4.0 the listed companies come from `fontes/acoes.csv` (see `fontes/LEIAME.md`), only the rows marked `conferido` and `usar_no_pack=sim`. `tools/gerar_termos.py` writes them into a delimited block at the end of the terms of `pack.yaml`; do not edit that block by hand, fix the CSV and run the generator again, which replaces only the block:

```
uv run --project ../transcript-normalizer python financas-ptbr/tools/gerar_termos.py --relatorio
```

Each generated term is one company (`class: companhia`), named as the CSV's `nome`, with its tickers, old tickers and other names as aliases, and `match: exact` (D-090): it is recognized only where it is written as listed, never by fuzzy, sound, plural or number words, and an old name (`Eletrobras`, `ELET3`) is recognized and left as said. A company the curated part already has is not generated, and the curated term is not touched. A name that is also an ordinary word (`tools/palavras_comuns.txt`) is recognized only in a video where stock-market terms appear (`context:`, D-086), and a short or ordinary single-word name only in its own case (`case_sensitive:`). The misrecognitions of each company are not generated: they come later, as variants seen in real videos.

## How it measures

Packs 0.3.9 and 0.4.0 give the same counts, column by column; the generated companies add recognitions of names spelled out, which leave the text as it was. Against each video's gold file, with engine 0.7.0 (0.4.0 is measured by loading the file with the engine's `min_engine` check turned off in the measuring process, since 0.8.0 is not released yet). The ruler is the engine's `evaluate_fixture(fixture, pack)`, with the pack loaded with an empty learned layer (`load_pack(path, learned=Learned())`), so nothing a user taught the tool counts; only what reaches `normalized.txt` is scored (D-048), and pack fit (D-054) is not applied:

| video | rows in scope | hits | misses | false positives | aliases recognized | aliases wrongly substituted |
|---|---|---|---|---|---|---|
| video 1 | 167 | 123 | 44 | 12 | 8 | 0 |
| video 2 | 222 | 168 | 54 | 3 | 37 | 0 |
| video 3 | 45 | 44 | 1 | 2 | 15 | 0 |
| video 4 | 119 | 105 | 14 | 4 | 38 | 0 |

Until 0.3.9 this table showed the numbers of 0.3.8 (video 1: 145 hits, video 2: 211). The numbers of 0.3.8 in the next paragraph are kept as they were measured then.

0.3.8 gives OPEX back its variant `Ox`, only in a video where CAPEX appears (D-086): video 1 regains three rows (142 → 145 hits), with false positives unchanged. Out of the domain, forced past pack fit, 0.3.8 changes no text. On a first video from another field (D-035) the one annotation is a recognition (`tir` → TIR) that leaves the text as it was; its `Ox` is the Northeastern `oxe`, and with no CAPEX in the video it is not even proposed. On a second one (D-035), nothing is applied; the words that only sound like BR Partners are asked, never applied (D-060). Pack fit (D-054) finds 15 to 44 of its terms with confidence in the four videos, 1 in the first video from another field and 0 in the second, so the engine would not apply it there at all.

0.4.0, forced past pack fit on that second video and on a third from another field, applies nothing and proposes nothing that 0.3.9 did not; pack fit stays at 0 on both. In the four videos it adds 10 recognitions, none scored: Petrobras, Sanepar, Copel, Light, Axia, B3, and one wrong one that leaves the text as it was, `Vale a pena`. The company Fica is left out of the pack (`usar_no_pack=nao`): at the start of a sentence, `Fica` is an ordinary word.

The table above runs `evaluate_fixture` from the engine repository against this repository's file. `uv run python scripts/measure.py` there measures the copy bundled with the engine instead, which in engine 0.7.0 is still 0.3.8. The decision numbers (D-0xx) point into its `docs/DECISIONS.md`.

## Maintainers

See `MAINTAINERS`.

0.3.9 removes 32 variants that are an ordinary word or phrase, too short, or the same as another term (D-032): CEMIG (`esse amigo`, `me caiu`, `do 100`, `sem amig`, `SEMI`, `CIC`), CPF, `taa`, `arte`, `bit` and `EBA` (EBITDA), `B`, `bit` and `be` (bilhão), `rap` and `rápid` (RAP), `valo`, `TR`, `índia`, `End`, `Word`, `NSS`, `Lu`, `anel`, `deck`, `ESA`, `Roy` and `ROI` (ROE), `ROK`, `Rid`, `Portou` and `partner` (BR Partners). The terms and their aliases stay, and no conditional form takes their place: if one of these garbles comes back, it is added again from a later transcript, with a gold file. The unit rule "number + B/bit/bi/be" is unchanged.
