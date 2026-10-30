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

`financas-ptbr` also ships inside the tool, to work offline. From 0.7.0 it is included, not installed: nothing is active until you pick a pack, and installing the included one needs no connection (`pack install financas-ptbr`, or choosing it in the menu). `pack list` shows the packs installed, those included in the tool and those here, each marked. `pack update` takes the newest version your transcript-normalizer can use: 0.8.0 and later get financas-ptbr 0.4.0, 0.7.x get 0.3.9, older versions keep 0.3.7.

## Proposing a change to a pack

The easy way is to let the tool do it: after you review a run, `transcript-normalizer pack propose --pack <name>` proposes what you taught it, and `pack propose --whole <name>` (menu: Packs → Contribute a pack) proposes your edited copy; each opens a prefilled issue here. Without a GitHub account, export your copy (Packs → Export a pack file, or `pack export <name> --to <folder>`) and send it to a maintainer of the pack. By hand, open a pull request that edits `<name>/pack.yaml`, says where each new form was seen, bumps the version, and updates `index.json`, with `min_engine` when the change needs a newer engine. [CONTRIBUTING.md](CONTRIBUTING.md) has each step, how to measure a pack and the review checklist.

## Proposing a new pack

Open a pull request that adds `<name>/` with `pack.yaml`, a `README.md` that says what the pack covers and how it was measured, and `MAINTAINERS` with at least one name, plus its entry in `index.json`. Name it `<domain>-<language>`, like `financas-ptbr`, and check before proposing that it applies nothing to a video from another field. See [CONTRIBUTING, section 3](CONTRIBUTING.md#3-proposing-a-new-pack).

## Who decides

Each pack directory lists its maintainers in `MAINTAINERS`. They review the pull requests and issues for their pack, and a change to a pack needs the approval of one of them. A new pack brings its own maintainers.

The engine repository never edits pack content. It ships a copy of `financas-ptbr` as its offline default, taken from here at a released version, and the engine's tests use frozen copies of their own.

## License

MIT, like the engine. See `LICENSE`.
