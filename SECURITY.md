# Security

This repository holds the packs that transcript-normalizer installs and the `index.json` that lists them. `pack install` and `pack update` read that index, download the file at the entry's `path`, and write it to `packs/<name>.yaml` only if its sha256 matches the entry's `sha256`; otherwise they write nothing. Pack names are limited to lowercase letters, digits and hyphens, and pack files are read with `yaml.safe_load`. What follows is about what could get past those checks. It refers to transcript-normalizer 0.8.1.

## What to report here

- An entry in `index.json` whose `sha256` does not match the file at its `path`.
- A way to make `pack install` or `pack update` install a file other than the one published here.
- A pack that makes the engine run something, read or write a file it should not, or hang when it loads the pack.
- A contribution (pull request, exported pack, `contributions/` file) that hides malicious content.
- Data in a pack's `fontes/` that may not be redistributed.

A wrong term or a correction the pack should not make is not a security problem. Open a normal issue, as [CONTRIBUTING.md](CONTRIBUTING.md) says.

If the problem is in the engine and not in a pack, report it as the engine's [SECURITY.md](https://github.com/Tatiwel/transcript-normalizer/blob/main/SECURITY.md) says.

## How to report

Privately, with the "Report a vulnerability" button on this repository's [security advisories page](https://github.com/Tatiwel/transcript-normalizer-packs/security/advisories/new). If you cannot use it, email danieldandez@gmail.com.

Never in a public issue, pull request or discussion.

## Versions covered

The pack versions that `index.json` serves today. An older version that is no longer in the index is not covered.

## What to expect

The project has one maintainer. You get an acknowledgement within 7 days. A fix ships as a new version of the pack in `index.json`.
