# transcript-normalizer-packs

Domain packs for [transcript-normalizer](https://github.com/Tatiwel/transcript-normalizer).

A pack is the list of terms the tool may touch in a transcript: each term's correct spelling, its other legitimate names (aliases) and the ways speech recognition garbles it (variants). Nothing outside a pack is ever changed. The engine lives in the other repository. This one holds the domain content, one directory per pack:

```
financas-ptbr/
  pack.yaml      the pack itself
  README.md      what it covers, where its terms came from, how it measures
  MAINTAINERS    who reviews changes to it
index.json       every pack: name, version, language, description, path, sha256,
                 and min_engine when it needs a recent transcript-normalizer
```

## Installing a pack

With transcript-normalizer 0.4.2 or later:

```
transcript-normalizer pack list
transcript-normalizer pack install financas-ptbr
transcript-normalizer pack update
```

`pack list` reads `index.json` from this repository. `pack install` downloads the pack into your `packs/` directory and checks it against the sha256 in the index before writing it. `pack update` installs a newer version of every pack you have installed from here. A pack you edited yourself is left alone.

Without the command, download `<name>/pack.yaml`, save it as `packs/<name>.yaml` where you run the tool, and pass it with `--pack` or pick it in the menu.

`financas-ptbr` also ships inside the tool, as the default that works offline. An installed copy wins over the bundled one.

## Proposing a change to a pack

The easy way is to let the tool do it. After you review a run (`normalize --review`, or the menu), your answers are in your learned layer. `transcript-normalizer pack propose --pack <name>` shows what you would contribute: term, form and decision, never the transcript. Once you confirm, it writes `contributions/<pack>-<date>.yaml` and opens a prefilled issue here. A maintainer of that pack reviews it.

By hand, open a pull request that edits `<name>/pack.yaml`:

1. Follow the curation rules in the engine's [CONTRIBUTING, section 2](https://github.com/Tatiwel/transcript-normalizer/blob/main/CONTRIBUTING.md#2-building-a-domain-pack): an alias is something the speaker really said, a variant is the recognizer's mistake; no one- or two-letter strings; no ordinary words as variants.
2. Say where each new form was seen: video, timestamp, and the line it is on.
3. Bump the pack's `version` (patch for data, minor for a change of shape) and say in the comment at the top of the pack what the version adds.
4. Update the pack's entry in `index.json`: `version`, and `sha256` (`sha256sum <name>/pack.yaml`).
5. If the change uses something an older transcript-normalizer does not understand (`context:` and `unless_near:` need 0.7.0), say so in two places: `min_engine: "0.7.0"` at the top of `<name>/pack.yaml`, so a copy saved by hand is refused by an engine too old for it, and `"min_engine": "0.7.0"` in its `index.json` entry, so `pack list`, `pack install` and `pack update` skip it there with the reason. Versions up to 0.6.5 ignore `min_engine` and take the last entry of a pack in `index.json`. So keep the previous version for them: move its file to `<name>/<old version>/pack.yaml` (its sha256 does not change) and list it as a second entry, after the new one, without `min_engine`:

   ```json
   {"name": "financas-ptbr", "version": "0.3.8", "min_engine": "0.7.0", "path": "financas-ptbr/pack.yaml", "sha256": "…", "language": "pt-BR", "description": "…"},
   {"name": "financas-ptbr", "version": "0.3.7", "path": "financas-ptbr/0.3.7/pack.yaml", "sha256": "…", "language": "pt-BR", "description": "…"}
   ```

   An engine from 0.7.0 on takes the newest version it can use; an older one keeps the last entry. Publish such a change only once that engine version is released.

## Proposing a new pack

Open a pull request that adds a directory: `<name>/pack.yaml`, a `README.md` that says what the pack covers and how it was measured, and `MAINTAINERS` with at least one name. Add its entry to `index.json`. Name it `<domain>-<language>`, like `financas-ptbr`. Before proposing, run it on a video from a different field (the silence run, CONTRIBUTING 2.4): it should apply nothing there.

## Who decides

Each pack directory lists its maintainers in `MAINTAINERS`. They review the pull requests and issues for their pack, and a change to a pack needs the approval of one of them. A new pack brings its own maintainers.

The engine repository never edits pack content. It ships a copy of `financas-ptbr` as its offline default, taken from here at a released version, and the engine's tests use frozen copies of their own.

## License

MIT, like the engine. See `LICENSE`.
