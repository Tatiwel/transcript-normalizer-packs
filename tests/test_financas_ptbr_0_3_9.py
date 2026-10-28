"""financas-ptbr 0.3.9: variants that are ordinary words or collide with another term are gone (D-032).

Run with the engine's environment, from this repository:

    uv run --project ../transcript-normalizer pytest -q tests
"""

import hashlib
import json
from pathlib import Path

import pytest

from transcript_normalizer import find_annotations, load_pack, parse_caption, resolve_overlaps
from transcript_normalizer.core.pack import Learned

ROOT = Path(__file__).resolve().parents[1]
PACK_FILE = ROOT / "financas-ptbr" / "pack.yaml"

#: term -> the variants 0.3.9 removed. The term stays, and so do its aliases.
REMOVED = {
    "CEMIG": ["esse amigo", "me caiu", "do 100", "sem amig", "SEMI", "CIC"],
    "CPFL": ["CPF"],
    "Taesa": ["taa"],
    "Ártica": ["arte"],
    "EBITDA": ["bit", "EBA"],
    "bilhão": ["bit", "B", "be"],
    "RAP": ["rap", "rápid"],
    "valuation": ["valo"],
    "tri": ["TR"],
    "Engie": ["índia", "End"],
    "Ward": ["Word"],
    "Adeus INSS": ["NSS"],
    "Leo": ["Lu"],
    "ANEEL": ["anel"],
    "DEC": ["deck"],
    "ISA": ["ESA"],
    "ROE": ["ROI", "Roy"],
    "ROIC": ["ROK"],
    "ROI": ["Rid"],
    "BR Partners": ["Portou", "partner"],
}


@pytest.fixture(scope="module")
def pack():
    return load_pack(PACK_FILE, learned=Learned())


def test_version_and_index():
    entries = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))["packs"]
    assert [e["version"] for e in entries] == ["0.3.9", "0.3.7"]
    assert entries[0]["min_engine"] == "0.7.0" and "min_engine" not in entries[1]
    assert entries[0]["sha256"] == hashlib.sha256(PACK_FILE.read_bytes()).hexdigest()
    assert 'min_engine: "0.7.0"' in PACK_FILE.read_text(encoding="utf-8")


@pytest.mark.parametrize("term", REMOVED)
def test_removed_variants_are_gone_and_the_term_stays(pack, term):
    found = pack.term_named(term)
    assert found is not None
    kept = {pack.normalize(v) for v in found.variants}
    assert not kept & {pack.normalize(v) for v in REMOVED[term]}


def test_kept_variants_stay(pack):
    assert "no bank" in pack.term_named("Nubank").variants
    assert "PCA" in pack.term_named("IPCA").variants
    assert "apo" in pack.term_named("IPO").variants
    assert "Ox" in pack.term_named("OPEX").variants


def test_esse_amigo_is_not_cemig(pack):
    caption = (
        "0:01 Hoje o EBITDA da empresa subiu e o dividend yield também.\n"
        "0:08 Esse amigo meu olhou o preço teto e o valuation antes de comprar.\n"
        "0:15 Ele disse: me caiu bem, do 100 por cento, sem amigo nenhum.\n"
        "0:22 A Selic e o payout pesaram, e o CAPEX também.\n"
    )
    transcript = parse_caption(caption)
    annotations = resolve_overlaps(find_annotations(transcript, pack))
    assert not [a for a in annotations if a.term == "CEMIG"]
    assert {a.term for a in annotations if a.applied} >= {"EBITDA", "valuation", "preço teto"}
