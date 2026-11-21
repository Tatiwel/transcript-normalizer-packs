"""financas-ptbr 0.4.1: BR Partners matches only as written (D-090).

Run with the engine's environment, from this repository:

    uv run --project ../transcript-normalizer pytest -q tests
"""

from pathlib import Path

import yaml

from transcript_normalizer import find_annotations, load_pack, parse_caption, resolve_overlaps
from transcript_normalizer.core.pack import Learned

ROOT = Path(__file__).resolve().parents[1]
PACK_FILE = ROOT / "financas-ptbr" / "pack.yaml"


def br_partners(text):
    pack = load_pack(PACK_FILE, learned=Learned())
    found = resolve_overlaps(find_annotations(parse_caption(f"0:01 {text}\n"), pack))
    return [(a.original, a.applied) for a in found if a.term == "BR Partners"]


def test_br_partners_is_exact():
    data = yaml.safe_load(PACK_FILE.read_text(encoding="utf-8"))
    term = next(t for t in data["terms"] if t["term"] == "BR Partners")
    assert term["match"] == "exact"


def test_ordinary_words_no_longer_reach_br_partners():
    # From a lesson transcribed locally, where 0.4.0 applied or asked all of these.
    for text in ("e os aportes do mês", "fechou as portas", "deixou para trás", "vou aportar só isso"):
        assert br_partners(text) == [], text


def test_the_listed_forms_still_do():
    assert br_partners("o BTG e o BR Portness") == [("BR Portness", True)]
    assert [form for form, _ in br_partners("comprei BRBI11 ontem")] == ["BRBI11"]  # an alias
