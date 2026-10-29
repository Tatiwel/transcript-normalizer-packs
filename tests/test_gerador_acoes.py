"""financas-ptbr/tools/gerar_termos.py and the 0.4.0 it wrote.

Run with the engine's environment, from this repository:

    uv run --project ../transcript-normalizer pytest -q tests

The pack needs transcript-normalizer 0.8.0 (`min_engine`, D-090). While the
engine checkout still says 0.7.0, the tests that load it turn the check off in
this process only; no file changes.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

import transcript_normalizer.core.pack as pack_module
from transcript_normalizer import find_annotations, load_pack, parse_caption, resolve_overlaps
from transcript_normalizer.core.pack import Learned

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "financas-ptbr" / "tools"
PACK_FILE = ROOT / "financas-ptbr" / "pack.yaml"
PACK_0_3_9 = ROOT / "financas-ptbr" / "0.3.9" / "pack.yaml"
ACOES = ROOT / "financas-ptbr" / "fontes" / "acoes.csv"
PALAVRAS = TOOLS / "palavras_comuns.txt"

_spec = importlib.util.spec_from_file_location("gerar_termos", TOOLS / "gerar_termos.py")
gerar_termos = importlib.util.module_from_spec(_spec)
sys.modules["gerar_termos"] = gerar_termos  # dataclasses look their module up there
_spec.loader.exec_module(gerar_termos)

#: The companies the curated part already has (the curated term wins).
CURATED_COMPANIES = [
    "Cemig", "CPFL Energia", "Taesa", "Klabin", "Sabesp", "Copasa", "Engie",
    "Auren Energia", "Banco BTG Pactual", "BR Partners", "ISA Energia",
]


def gerar(pack_text: str | None = None):
    return gerar_termos.gerar(
        pack_text if pack_text is not None else PACK_FILE.read_text(encoding="utf-8"),
        ACOES.read_text(encoding="utf-8"),
        PALAVRAS.read_text(encoding="utf-8"),
    )


@pytest.fixture(scope="module")
def pack():
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pack_module, "check_engine", lambda path, data: None)
        yield load_pack(PACK_FILE, learned=Learned())


def annotations(pack, caption: str):
    return resolve_overlaps(find_annotations(parse_caption(caption), pack))


# --------------------------------------------------------------------------- the generator


def test_two_runs_write_the_same_file(tmp_path):
    first, second = tmp_path / "um.yaml", tmp_path / "dois.yaml"
    for target in (first, second):
        target.write_bytes(PACK_FILE.read_bytes())
        assert gerar_termos.main(["--pack", str(target), "--acoes", str(ACOES), "--palavras", str(PALAVRAS)]) == 0
    assert first.read_bytes() == second.read_bytes()


def test_the_committed_pack_is_what_the_generator_writes():
    novo, _ = gerar()
    assert novo == PACK_FILE.read_text(encoding="utf-8")


def test_regenerating_changes_only_the_block():
    texto = PACK_FILE.read_text(encoding="utf-8")
    inicio, fim = texto.index(gerar_termos.INICIO), texto.index(gerar_termos.FIM) + len(gerar_termos.FIM)
    # A curated edit before the block, and a stale block, as a later run would find them.
    editado = "# uma linha curada nova\n" + texto[:inicio] + gerar_termos.INICIO + "  # velho\n" + gerar_termos.FIM + texto[fim:]
    novo, _ = gerar(editado)
    i, f = novo.index(gerar_termos.INICIO), novo.index(gerar_termos.FIM) + len(gerar_termos.FIM)
    assert novo[:i] == "# uma linha curada nova\n" + texto[:inicio]
    assert novo[f:] == texto[fim:]
    assert novo[i:f] == texto[inicio:fim]


def test_without_a_block_it_goes_before_unit_rules():
    sem = gerar_termos.sem_bloco(PACK_FILE.read_text(encoding="utf-8"))
    novo, _ = gerar(sem)
    assert novo == PACK_FILE.read_text(encoding="utf-8")


# --------------------------------------------------------------------------- the curated term wins


def curated_terms(path: Path) -> list[dict]:
    return yaml.safe_load(gerar_termos.sem_bloco(path.read_text(encoding="utf-8")))["terms"]


def test_the_curated_part_is_0_3_9_untouched():
    assert curated_terms(PACK_FILE) == curated_terms(PACK_0_3_9)


def test_a_curated_company_is_not_generated():
    _, relatorio = gerar()
    pulados = {nome for nome, _ in relatorio.pulados}
    assert set(CURATED_COMPANIES) <= pulados
    assert not {g.nome for g in relatorio.gerados} & set(CURATED_COMPANIES)


def test_no_generated_form_is_a_curated_form():
    dobra = gerar_termos.dobra
    curated = {dobra(str(f)) for t in curated_terms(PACK_FILE)
               for f in [t["term"], *(t.get("aliases") or ()), *(t.get("variants") or ())]}
    _, relatorio = gerar()
    clashes = [(g.nome, f) for g in relatorio.gerados for f in [g.nome, *g.aliases] if dobra(f) in curated]
    assert clashes == []


def test_cemig_is_still_the_curated_term(pack):
    found = annotations(pack, "0:01 A CEMIG e a CMIG4 pagaram dividendo, e o EBITDA subiu.\n")
    assert {a.term for a in found if a.original in ("CEMIG", "CMIG4")} == {"CEMIG"}


# --------------------------------------------------------------------------- old names, exact match, context


def test_eletrobras_is_not_rewritten_as_axia(pack):
    caption = (
        "0:01 Em 2024 a Eletrobras e a ELET3 pagaram dividendo.\n"
        "0:05 O EBITDA da Eletro Bras e da Eletrobrás subiu.\n"
    )
    found = annotations(pack, caption)
    assert not [a for a in found if a.replacement == "Axia Energia"]
    axia = [a for a in found if a.term == "Axia Energia"]
    assert [a.original for a in axia] == ["Eletrobras", "ELET3", "Eletrobrás"]
    assert all(a.replacement == a.original for a in axia)


def test_a_generated_name_is_not_reached_by_similarity(pack):
    caption = (
        "0:01 Os prions se multiplicam e conseguem escapar; um brasileiro relatou o caso.\n"
        "0:05 A energia da usina, a técnica e a revisão.\n"
    )
    generated = {g.nome for g in gerar()[1].gerados}
    assert [a for a in annotations(pack, caption) if a.term in generated] == []


def test_a_house_that_is_blue_is_not_azul():
    caption = "0:01 A casa é azul.\n0:04 Azul é a cor do céu.\n"
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(pack_module, "check_engine", lambda path, data: None)
        pack = load_pack(PACK_FILE, learned=Learned())
    assert not [a for a in annotations(pack, caption) if a.term == "Azul"]


def test_azul_is_found_where_the_market_is_talked_about(pack):
    caption = (
        "0:01 A Azul divulgou o EBITDA do trimestre.\n"
        "0:05 O dividendo e o valuation ainda preocupam, e a azul do céu não.\n"
    )
    azul = [a for a in annotations(pack, caption) if a.term == "Azul"]
    assert [a.original for a in azul] == ["Azul"]
