# Contributing

Everyone taking part here follows the [Code of Conduct](CODE_OF_CONDUCT.md).

How to propose a change to a pack or a new pack, how to measure it, and how a maintainer reviews it. The commands are those of transcript-normalizer 0.8.1. The curation rules themselves (what is an alias, what is a variant, what stays out) are in the engine's [CONTRIBUTING, section 2](https://github.com/Tatiwel/transcript-normalizer/blob/main/CONTRIBUTING.md#2-building-a-domain-pack); this file does not repeat them.

## Contents

1. [Contributing without git](#1-contributing-without-git)
2. [Proposing a change by pull request](#2-proposing-a-change-by-pull-request)
3. [Proposing a new pack](#3-proposing-a-new-pack)
4. [Measuring a pack](#4-measuring-a-pack)
5. [Running the tests](#5-running-the-tests)
6. [Generated packs](#6-generated-packs)
7. [Review checklist](#7-review-checklist)

## 1. Contributing without git

You need the tool, not git. Edit your copy of the pack in the menu (Packs → Edit a pack, which offers to make your own copy first) or with `pack copy`, `pack add-term` and `pack edit-term`. Then write it to a file:

- menu: Packs → Export a pack file, and pick a folder;
- command: `transcript-normalizer pack export <name> --to <folder>`.

Either writes `<name>-<version>.yaml`. Send that file to a maintainer of the pack (the names are in `<name>/MAINTAINERS`), with:

- the links of the videos you used;
- for each new form, the video and the minute where it is.

The maintainer opens the pull request. The exported file is not dropped over `<name>/pack.yaml`: the editor rewrites the file, keeps only the comment block at the top, drops the markers of a generated block (section 6) and adds `based_on` and `local_edits`. The maintainer carries the changed terms into the pack by hand.

What you taught the tool in reviews can be sent the same way: `transcript-normalizer pack propose --pack <name>` shows it (term, form and decision, never the transcript), and on a yes writes `contributions/<name>-<date>.yaml`. That file can be sent too.

With a GitHub account, let the tool open the issue for you:

- a whole pack, or your edited copy of one: Packs → Contribute a pack, or `transcript-normalizer pack propose --whole <name>`. For a copy it proposes only what changed since its base. It writes `contributions/<name>-<version>.yaml` and opens a prefilled issue here, "New pack: <name>" or "Update: <name>";
- your review answers: `transcript-normalizer pack propose --pack <name>`. After you review a run (`normalize --review`, or the menu), your answers are in your learned layer; this proposes what the pack does not already have, writes `contributions/<name>-<date>.yaml` and opens a prefilled issue here. The menu offers it after a review.

Nothing leaves your computer until you submit the issue yourself. A maintainer of that pack reviews it.

## 2. Proposing a change by pull request

Open a pull request that edits `<name>/pack.yaml`:

1. Follow the curation rules in the engine's [CONTRIBUTING, section 2](https://github.com/Tatiwel/transcript-normalizer/blob/main/CONTRIBUTING.md#2-building-a-domain-pack): an alias is something the speaker really said, a variant is the recognizer's mistake; no one- or two-letter strings; no ordinary words as variants.
2. Say where each new form was seen: video, timestamp, and the line it is on.
3. Bump the pack's `version` (patch for data, minor for a change of shape) and say in the comment at the top of the pack what the version adds.
4. Update the pack's entry in `index.json`: `version`, and `sha256` (`sha256sum <name>/pack.yaml`).
5. Measure it (section 4) and update the table in the pack's README. A change should not make any column worse than the previous version.
6. Run the tests (section 5).

If the pack has a generated block, a change to it goes into the source files, not the block (section 6).

### When a change needs a newer engine

If the change uses something an older transcript-normalizer does not understand (`context:` and `unless_near:` need 0.7.0, `match:` and `case_sensitive:` need 0.8.0), say so in two places: `min_engine: "0.7.0"` at the top of `<name>/pack.yaml`, so a copy saved by hand is refused by an engine too old for it, and `"min_engine": "0.7.0"` in its `index.json` entry, so `pack list`, `pack install` and `pack update` skip it there with the reason. Versions up to 0.6.5 ignore `min_engine` and take the last entry of a pack in `index.json`. So keep the previous version for them: move its file to `<name>/<old version>/pack.yaml` (its sha256 does not change) and list it as a second entry, after the new one, without `min_engine`:

```json
{"name": "financas-ptbr", "version": "0.3.8", "min_engine": "0.7.0", "path": "financas-ptbr/pack.yaml", "sha256": "…", "language": "pt-BR", "description": "…"},
{"name": "financas-ptbr", "version": "0.3.7", "path": "financas-ptbr/0.3.7/pack.yaml", "sha256": "…", "language": "pt-BR", "description": "…"}
```

An engine from 0.7.0 on takes the newest version it can use; an older one keeps the last entry. Publish such a change only once that engine version is released.

When `min_engine` goes up again, do the same with the version it replaces: move its file to `<name>/<its version>/pack.yaml` and add its entry, with its own `min_engine`, between the new one and the older ones. The newest comes first, and the last entry is always the one without `min_engine`. `financas-ptbr` does this today: 0.4.0 (0.8.0), then 0.3.9 (0.7.0), then 0.3.7. A pack that uses `match:` or `case_sensitive:` also bumps its minor version (engine CONTRIBUTING 2.3b), and the tests check that it says 0.8.0 in both places (section 5).

## 3. Proposing a new pack

Open a pull request that adds a directory:

- `<name>/pack.yaml`, the pack. A field template is the easy start: `transcript-normalizer pack create --template <field> --name <name> --lang <code>`;
- `<name>/README.md`, which says what the pack covers, where its terms came from and how it was measured (section 4);
- `<name>/MAINTAINERS`, with at least one name. These people review the pack's changes from then on.

Add its entry to `index.json` (`name`, `version`, `language`, `description`, `path`, `sha256`, and `min_engine` when it needs one). Name it `<domain>-<language>`, like `financas-ptbr`. Before proposing, run it on a video from a different field (the silence run, section 4): it should apply nothing there. A new pack may bring its own tests (section 5).

## 4. Measuring a pack

Two measures: what the pack does where it does not belong, and what it gets right where it does.

### The silence run

Take a caption from a video of another field (`transcript-normalizer fetch <url>` writes `runs/<id>/legenda.txt`). Normalize it with the pack twice:

```
transcript-normalizer normalize runs/<id>/legenda.txt --pack <name>/pack.yaml --summary
transcript-normalizer normalize runs/<id>/legenda.txt --pack <name>/pack.yaml --summary --force
```

Without `--force` is what a user sees: the engine counts the pack's terms it finds with confidence, and below three it changes nothing ("does not seem to fit this transcript … nothing applied"). With `--force` the pack is applied anyway: the worst case. The target is zero applied in both: without `--force`, the message above, or `0 applied` if the pack does fit; with it, `corrected 0` and `applied, please confirm 0` in the summary, and `0 applied` in `report.txt`. A name that only sounds like a pack term is suggested, never applied; suggestions do not count against the pack. Any applied correction there is a false positive by definition (engine CONTRIBUTING 2.4).

`--out <dir>` writes elsewhere than `runs/<id>/`. The pack is named by its file name, so the messages say `pack` for `<name>/pack.yaml`; that is expected.

### Against a gold file

A fixture is a video whose caption was checked by hand; its `gold.csv` says what the tool must get right. The engine's [CONTRIBUTING, section 3](https://github.com/Tatiwel/transcript-normalizer/blob/main/CONTRIBUTING.md#3-building-a-fixture-and-measuring) says how to build one. The engine's `fixtures/` holds those of `financas-ptbr`.

Score a pack with `evaluate_fixture(fixture, pack)`, and load the pack with an empty learned layer, so nothing a user taught the tool counts. With the engine checked out beside this repository:

```python
from pathlib import Path

from transcript_normalizer import load_pack
from transcript_normalizer.core.pack import Learned
from transcript_normalizer.evaluate import evaluate_fixture, fixtures

pack = load_pack(Path("financas-ptbr/pack.yaml"), learned=Learned())
for fixture in fixtures(Path("../transcript-normalizer/fixtures")):
    print(fixture.name, evaluate_fixture(fixture, pack).counts())
```

```
uv run --project ../transcript-normalizer python measure.py
```

It prints one line per fixture: rows in scope, hits, misses, false positives, aliases recognized and aliases wrongly substituted. For `financas-ptbr` they are the numbers of the table in its README. Only what reaches `normalized.txt` is scored, and pack fit is not applied. `render(result)`, from the same module, prints the misses and the false positives one by one.

Write the numbers in the pack's README, with the engine version they were measured with, and say what moved since the previous version and why.

## 5. Running the tests

From this repository, with the engine checked out beside it:

```
uv run --project ../transcript-normalizer pytest -q tests
```

`tests/test_pack_schema.py` runs on every pack in `index.json`, with no change for a new one:

- a pack version that uses `match:` says `min_engine` 0.8.0 or later, both in its file and in its index entry;
- no form of the current `<name>/pack.yaml` (term, alias or variant) has more words than the matcher compares (3). Such a form never matches.

The other files hold one pack's own tests: `test_gerador_acoes.py` checks the generator of `financas-ptbr` and the 0.4.0 it wrote, `test_financas_ptbr_0_3_9.py` the variants 0.3.9 removed. A new pack can bring its own, as `tests/test_<name>_<what>.py`, run the same way.

## 6. Generated packs

Part of a pack may be generated from a list, as the listed companies of `financas-ptbr` are. The pattern:

```
financas-ptbr/
  fontes/        the source data, and LEIAME.md: columns, rules, origin
  tools/         the generator, and the lists it reads
```

- **A delimited block.** The generator writes its terms between two marker comments at the end of the terms, and replaces only that block; the rest of `pack.yaml` stays byte for byte. Nobody edits the block by hand: fix the source and run the generator again.
- **The curated part wins.** A generated term that collides with a curated one (same name, alias or code) is not generated, and the curated term is not touched.
- **Only checked rows.** Only rows marked as checked against a source, and marked for the pack, go in (in `financas-ptbr`: `status=conferido` and `usar_no_pack=sim`).
- **`match: exact` by default.** A generated term matches only by equality with its own forms: no fuzzy, sound, plural or number-word match. Its misrecognitions come later, as variants seen in real videos. This needs `min_engine: "0.8.0"` (section 2).
- **Deterministic, no network.** The same input always gives the same file.
- **`--verificar` and `--relatorio`.** `--verificar` writes nothing and exits with 1 if `pack.yaml` would change; it must exit 0 before a merge. `--relatorio` lists what was skipped and why.

For `financas-ptbr`:

```
uv run --project ../transcript-normalizer python financas-ptbr/tools/gerar_termos.py --verificar
uv run --project ../transcript-normalizer python financas-ptbr/tools/gerar_termos.py --relatorio
```

**License.** The engine downloads only `pack.yaml`, but this repository redistributes everything in `fontes/` with the pack. The source of the data must allow that. Record where it came from, and on what date, in `fontes/LEIAME.md` (or a README there). See [`financas-ptbr/fontes/LEIAME.md`](financas-ptbr/fontes/LEIAME.md) for an example.

## 7. Review checklist

For maintainers. A pack file is named by its file name, so check a copy named after the pack:

```
mkdir -p /tmp/check && cp <name>/pack.yaml /tmp/check/<name>.yaml
TRANSCRIPT_NORMALIZER_HOME=/tmp/check transcript-normalizer pack import /tmp/check/<name>.yaml
```

- [ ] `pack import` loads the pack without error.
- [ ] Each new variant has an origin (video, minute, line) and is a caption error, not what the speaker really said; a form the speaker said is an alias.
- [ ] No new form of one or two letters; no ordinary word as a variant unless it has a `context:`; no form of more than 3 words.
- [ ] Silence run: zero applied, with and without `--force` (section 4).
- [ ] The measurement is in the pack's README, with the engine version, and no column is worse than in the previous version.
- [ ] `version` is bumped (patch for data, minor for shape) and the comment at the top of the pack says what it adds.
- [ ] If the pack needs a newer engine: `min_engine` in the file and in the index entry, and the previous version kept in `<name>/<old version>/pack.yaml` with its own entry, the last entry without `min_engine` (section 2).
- [ ] `sha256` in `index.json` matches `sha256sum <name>/pack.yaml`.
- [ ] The tests pass (section 5).
- [ ] New pack: `README.md` and `MAINTAINERS` are there, and the name is `<domain>-<language>`.
- [ ] `fontes/`: the source allows redistribution, its origin is recorded, and the generator's `--verificar` exits 0 (section 6).

After the merge, check what users get, in a clean folder:

```
export TRANSCRIPT_NORMALIZER_HOME=$(mktemp -d)
transcript-normalizer pack list
transcript-normalizer pack install <name>
transcript-normalizer pack list --installed
```

`pack list` should show the new version, and `pack install` install it after checking its sha256. A pack the program includes at the same version is installed from the program instead; `pack list` marks which. Before the merge, `--index file://$PWD/index.json` runs the same commands against your checkout.

For a security problem, do not open an issue: see [SECURITY.md](SECURITY.md).
