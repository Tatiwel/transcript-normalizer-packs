"""What every pack of this repository must hold, whatever its content.

Run with the engine's environment, from this repository:

    uv run --project ../transcript-normalizer pytest -q tests
"""

import json
from pathlib import Path

import pytest
import yaml

from transcript_normalizer.core.matcher import NGRAM_SIZES, tokenize
from transcript_normalizer.languages import pt_br

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))["packs"]
#: D-090: the first engine that knows `match: exact`.
EXACT_ENGINE = (0, 8, 0)
#: The current file of each pack: `<name>/pack.yaml`. Older versions are frozen.
CURRENT = sorted({ROOT / e["name"] / "pack.yaml" for e in ENTRIES})

#: (pack, term) -> its forms of more than NGRAM_SIZES words, curated before this test.
#: They never match, since the matcher compares windows of at most that many words.
KNOWN_LONG = {
    ("financas-ptbr", "dívida líquida"): ["dívida líquida sobre EBITDA"],
    ("financas-ptbr", "ANEEL"): ["agência nacional de energia elétrica"],
}


def version(text) -> tuple[int, ...]:
    return tuple(int(p) for p in str(text).split("."))


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@pytest.mark.parametrize("entry", ENTRIES, ids=lambda e: f"{e['name']}-{e['version']}")
def test_a_pack_that_matches_exactly_says_it_needs_0_8_0(entry):
    data = load(ROOT / entry["path"])
    if not any((t or {}).get("match") for t in data.get("terms") or ()):
        return
    assert version(data.get("min_engine", "0")) >= EXACT_ENGINE
    assert version(entry.get("min_engine", "0")) >= EXACT_ENGINE


def forms(term: dict) -> list[str]:
    return [str(f) for f in [term["term"], *(term.get("aliases") or ()), *(term.get("variants") or ())]]


def words(form: str) -> int:
    """Words as the matcher counts them in its windows."""
    return len(tokenize(form, pt_br.sentence_boundaries))


def cases():
    for path in CURRENT:
        for term in load(path).get("terms") or ():
            name = path.parent.name
            marks = ()
            if (name, str(term["term"])) in KNOWN_LONG:
                marks = pytest.mark.xfail(strict=True, reason="known: curated form of more than 3 words")
            yield pytest.param(path, term, marks=marks, id=f"{name}:{term['term']}")


@pytest.mark.parametrize(("path", "term"), list(cases()))
def test_no_form_has_more_words_than_the_matcher_compares(path, term):
    long = [f for f in forms(term) if words(f) > max(NGRAM_SIZES)]
    assert not long, f"{path.parent.name}: {term['term']!r} has forms that never match: {long}"
