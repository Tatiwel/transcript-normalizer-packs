"""Gera os termos de ações do financas-ptbr a partir de fontes/acoes.csv.

    uv run --project ../transcript-normalizer python financas-ptbr/tools/gerar_termos.py [--relatorio] [--verificar]

Lê só as linhas com `status=conferido` e `usar_no_pack=sim` e escreve um termo por
empresa num bloco delimitado do `pack.yaml`. Rodar de novo substitui só esse bloco;
o resto do arquivo fica idêntico, byte a byte. Determinístico e sem rede: a mesma
entrada dá sempre o mesmo arquivo. Dobra o texto com o módulo pt-BR da engine
(D-033), o mesmo que o matcher usa, por isso roda no ambiente da engine.

As regras, cada uma pela decisão da engine que a pede:

- Um termo por empresa, classe `companhia`, canônico igual à coluna `nome`. As classes
  da mesma empresa (CMIG3, CMIG4) viram aliases do mesmo termo.
- Tickers, tickers antigos e apelidos entram como aliases: casam só por igualdade
  exata e nunca são substituídos (D-020, D-025). Um nome antigo dito no vídeo
  ("Eletrobras", ELET3) é reconhecido e fica como foi dito.
- Um ticker cujo esqueleto fonético tem 5 letras ou mais (D-050) é descartado: a regra
  fonética lê os aliases da classe `companhia` (D-068) e o alcançaria.
- O curado ganha: uma empresa com nome, apelido ou ticker igual a uma forma de um
  termo curado, ou cujo nome contém o nome de uma companhia curada, não é gerada.
  Uma forma gerada igual a uma forma curada é descartada.
- Palavra comum só com contexto (D-032, D-086): `palavra_comum=sim`, nome de até 4
  letras, ou nome feito só de palavras comuns (`palavras_comuns.txt`). O canônico ganha
  `context:` com termos curados de mercado de ações. Um apelido não pode ter contexto
  (D-086), então um apelido curto ou comum é descartado.
- Uma forma que duas empresas geradas teriam é descartada das duas.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from transcript_normalizer.languages import pt_br

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "financas-ptbr" / "pack.yaml"
ACOES = ROOT / "financas-ptbr" / "fontes" / "acoes.csv"
PALAVRAS = Path(__file__).resolve().parent / "palavras_comuns.txt"

INICIO = "  # >>> início da parte gerada\n"
FIM = "  # <<< fim da parte gerada\n"
CABECALHO = (
    "  # gerado por financas-ptbr/tools/gerar_termos.py a partir de financas-ptbr/fontes/acoes.csv; não editar à mão\n"
    "  # Para corrigir um nome, corrija o CSV e rode o gerador de novo (financas-ptbr/fontes/LEIAME.md).\n"
)
ANTES_DE = "unit_rules:\n"

CLASSE = "companhia"
#: D-086: termos curados que só aparecem num vídeo de mercado de ações. Nenhum é
#: palavra comum, e nenhum tem forma curta que apareça fora do domínio (ficam de
#: fora TIR, por `tir uma`, IPO, por `apo`, IPCA, RI e yield).
CONTEXTO = (
    "dividendo",
    "dividend yield",
    "EBITDA",
    "valuation",
    "payout",
    "preço teto",
    "Selic",
    "P/VP",
    "ROE",
    "LPA",
    "tag along",
    "free float",
    "small cap",
    "CAPEX",
    "debêntures",
)
#: D-050: um esqueleto mais curto que isto não entra na regra fonética.
ESQUELETO_FONETICO = 5
#: Nomes de até tantas letras só entram com contexto.
CURTO = 4
#: Como começa o motivo de uma forma descartada por ser igual a outra.
COLISAO = "igual a "


def dobra(texto: str) -> str:
    return pt_br.normalize(texto)


def letras(dobrado: str) -> int:
    return len(dobrado.replace(" ", ""))


def ler_palavras(texto: str) -> frozenset[str]:
    palavras = set()
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if linha:
            palavras.add(dobra(linha))
    return frozenset(palavras)


def comum(dobrado: str, palavras: frozenset[str]) -> bool:
    """Cada palavra do nome é comum: da lista, do módulo pt-BR, ou uma letra só."""
    return all(p in palavras or p in pt_br.common_words or len(p) == 1 for p in dobrado.split())


def _lista(campo: str) -> list[str]:
    return [p.strip() for p in (campo or "").split(";") if p.strip()]


@dataclass
class Empresa:
    nome: str
    tickers: list[str] = field(default_factory=list)
    antigos: list[str] = field(default_factory=list)
    apelidos: list[str] = field(default_factory=list)
    palavra_comum: bool = False


def ler_acoes(texto: str) -> list[Empresa]:
    """As linhas conferidas e marcadas para o pack, uma empresa por `nome`."""
    empresas: dict[str, Empresa] = {}
    for linha in csv.DictReader(io.StringIO(texto)):
        if linha["status"] != "conferido" or linha["usar_no_pack"] != "sim":
            continue
        nome = linha["nome"].strip()
        e = empresas.setdefault(nome, Empresa(nome))
        e.tickers.append(linha["ticker"].strip())
        e.antigos += _lista(linha["tickers_antigos"])
        e.apelidos += _lista(linha["apelidos"])
        e.palavra_comum |= linha["palavra_comum"].strip() == "sim"
    for e in empresas.values():
        e.tickers = sorted(set(e.tickers))
        e.antigos = sorted(set(e.antigos) - set(e.tickers))
        e.apelidos = list(dict.fromkeys(e.apelidos))
    return sorted(empresas.values(), key=lambda e: (dobra(e.nome), e.nome))


def sem_bloco(texto: str) -> str:
    """O pack.yaml sem a parte gerada: só o que é curado à mão."""
    if INICIO not in texto:
        return texto
    antes, resto = texto.split(INICIO, 1)
    if FIM not in resto:
        raise ValueError("o pack.yaml tem o início da parte gerada e não tem o fim")
    return antes + resto.split(FIM, 1)[1]


def com_bloco(texto: str, bloco: str) -> str:
    """Troca a parte gerada por `bloco`; sem ela, põe o bloco antes de `unit_rules:`."""
    if INICIO in texto:
        antes, resto = texto.split(INICIO, 1)
        return antes + bloco + resto.split(FIM, 1)[1]
    linhas = texto.splitlines(keepends=True)
    if ANTES_DE not in linhas:
        raise ValueError(f"o pack.yaml não tem a linha {ANTES_DE.strip()!r} para pôr a parte gerada antes")
    i = linhas.index(ANTES_DE)
    return "".join(linhas[:i]) + bloco + "".join(linhas[i:])


@dataclass
class Gerado:
    nome: str
    aliases: list[str]
    protecao: list[str]  # por que o nome só entra com contexto; vazio: entra sem


@dataclass
class Relatorio:
    gerados: list[Gerado] = field(default_factory=list)
    pulados: list[tuple[str, str]] = field(default_factory=list)  # (empresa, termo curado e por quê)
    descartadas: list[tuple[str, str, str]] = field(default_factory=list)  # (empresa, forma, motivo)

    @property
    def protegidos(self) -> list[Gerado]:
        return [g for g in self.gerados if g.protecao]

    @property
    def colisoes(self) -> list[tuple[str, str, str]]:
        return [d for d in self.descartadas if d[2].startswith(COLISAO)]

    def resumo(self) -> str:
        return (
            f"termos gerados: {len(self.gerados)}\n"
            f"empresas puladas por já serem curadas: {len(self.pulados)}\n"
            f"nomes protegidos por contexto: {len(self.protegidos)}\n"
            f"formas descartadas por colisão: {len(self.colisoes)}\n"
            f"formas descartadas por outro motivo: {len(self.descartadas) - len(self.colisoes)}"
        )

    def completo(self) -> str:
        out = [self.resumo(), "", f"contexto de todos os nomes protegidos: {', '.join(CONTEXTO)}", ""]
        out.append("empresas puladas (o curado ganha):")
        out += [f"  {nome}: {motivo}" for nome, motivo in self.pulados]
        out += ["", "nomes protegidos por contexto:"]
        out += [f"  {g.nome}: {'; '.join(g.protecao)}" for g in self.protegidos]
        out += ["", "formas descartadas:"]
        out += [f"  {nome}: {forma!r} ({motivo})" for nome, forma, motivo in self.descartadas]
        return "\n".join(out)


def _curados(texto: str) -> list[dict]:
    return (yaml.safe_load(sem_bloco(texto)) or {}).get("terms") or []


def gerar(pack: str, acoes: str, palavras_texto: str) -> tuple[str, Relatorio]:
    """O novo texto do pack.yaml e o que foi feito."""
    palavras = ler_palavras(palavras_texto)
    curados = _curados(pack)
    nomes_curados = {str(t["term"]) for t in curados}
    faltam = [c for c in CONTEXTO if c not in nomes_curados]
    if faltam:
        raise ValueError(f"termos de contexto que não estão no pack: {', '.join(faltam)}")

    formas_curadas: dict[str, str] = {}  # forma dobrada -> termo curado
    for t in curados:
        for forma in [t["term"], *(t.get("aliases") or ()), *(t.get("variants") or ())]:
            formas_curadas.setdefault(dobra(str(forma)), str(t["term"]))
    companhias_curadas = [(dobra(str(t["term"])), str(t["term"])) for t in curados if t.get("class") == CLASSE]

    relatorio = Relatorio()
    gerados: list[Gerado] = []
    for e in ler_acoes(acoes):
        nome = dobra(e.nome)
        iguais = sorted(
            {f"{forma} = {formas_curadas[dobra(forma)]}"
             for forma in [e.nome, *e.apelidos, *e.tickers, *e.antigos] if dobra(forma) in formas_curadas}
        )
        contidos = [f"o nome contém {t}" for d, t in companhias_curadas if f" {d} " in f" {nome} "]
        if iguais or contidos:
            relatorio.pulados.append((e.nome, "; ".join(iguais + contidos)))
            continue

        vistos = {nome}
        aliases = []
        for forma, ticker in [(a, False) for a in e.apelidos] + [(t, True) for t in e.tickers + e.antigos]:
            d = dobra(forma)
            if d in vistos:
                continue
            vistos.add(d)
            motivo = None
            if ticker and len(pt_br.skeleton(forma)) >= ESQUELETO_FONETICO:
                motivo = f"ticker com esqueleto fonético {pt_br.skeleton(forma)!r}, a regra fonética o alcançaria"
            elif not ticker and letras(d) <= CURTO:
                motivo = f"apelido de até {CURTO} letras; alias não aceita contexto"
            elif not ticker and comum(d, palavras):
                motivo = "apelido feito de palavras comuns; alias não aceita contexto"
            if motivo:
                relatorio.descartadas.append((e.nome, forma, motivo))
            else:
                aliases.append(forma)

        protecao = []
        if e.palavra_comum:
            protecao.append("palavra_comum=sim")
        if letras(nome) <= CURTO:
            protecao.append(f"até {CURTO} letras")
        if comum(nome, palavras):
            protecao.append("palavra comum")
        gerados.append(Gerado(e.nome, aliases, protecao))

    # Nenhuma forma gerada igual a uma curada, nem a de outra empresa gerada.
    donos: dict[str, set[str]] = {}
    for g in gerados:
        for forma in [g.nome, *g.aliases]:
            donos.setdefault(dobra(forma), set()).add(g.nome)
    canonicos = {dobra(g.nome) for g in gerados}
    for g in gerados:
        mantidos = []
        for a in g.aliases:
            d = dobra(a)
            if d in formas_curadas:
                relatorio.descartadas.append((g.nome, a, f"{COLISAO}uma forma do termo curado {formas_curadas[d]}"))
            elif len(donos[d]) > 1 or d in canonicos:
                outros = ", ".join(sorted(donos[d] - {g.nome}))
                relatorio.descartadas.append((g.nome, a, f"{COLISAO}uma forma de outro termo gerado: {outros}"))
            else:
                mantidos.append(a)
        g.aliases = mantidos
    repetidos = sorted(d for d in canonicos if sum(dobra(g.nome) == d for g in gerados) > 1)
    if repetidos:
        raise ValueError(f"dois termos gerados com o mesmo nome: {', '.join(repetidos)}")

    relatorio.gerados = gerados
    relatorio.descartadas.sort(key=lambda x: (dobra(x[0]), x[0], dobra(x[1]), x[1]))
    return com_bloco(pack, _bloco(gerados)), relatorio


def _escalar(s: str, contexto: str) -> str:
    """`s` sem aspas quando o YAML o lê de volta igual nesse contexto; senão entre aspas."""
    aspas = json.dumps(s, ensure_ascii=False)
    try:
        if yaml.safe_load(contexto.format(s)) == yaml.safe_load(contexto.format(aspas)):
            return s
    except yaml.YAMLError:
        pass
    return aspas


def _bloco(gerados: list[Gerado]) -> str:
    contexto = ", ".join(_escalar(c, "k: [{}]") for c in CONTEXTO)
    linhas = [INICIO, CABECALHO]
    for g in gerados:
        linhas.append(f"  - term: {_escalar(g.nome, 'term: {}')}\n")
        linhas.append(f"    class: {CLASSE}\n")
        if g.aliases:
            linhas.append(f"    aliases: [{', '.join(_escalar(a, 'k: [{}]') for a in g.aliases)}]\n")
        if g.protecao:
            linhas.append(f"    context: {{{_escalar(g.nome, '{{{}: x}}')}: [{contexto}]}}\n")
    linhas.append(FIM)
    return "".join(linhas)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gera os termos de ações do financas-ptbr a partir de acoes.csv.")
    parser.add_argument("--pack", type=Path, default=PACK)
    parser.add_argument("--acoes", type=Path, default=ACOES)
    parser.add_argument("--palavras", type=Path, default=PALAVRAS)
    parser.add_argument("--relatorio", action="store_true", help="lista as empresas puladas, os nomes protegidos e as formas descartadas")
    parser.add_argument("--verificar", action="store_true", help="não escreve; sai com 1 se o pack.yaml mudaria")
    args = parser.parse_args(argv)

    atual = args.pack.read_text(encoding="utf-8")
    novo, relatorio = gerar(atual, args.acoes.read_text(encoding="utf-8"), args.palavras.read_text(encoding="utf-8"))
    print(relatorio.completo() if args.relatorio else relatorio.resumo())
    if args.verificar:
        if novo != atual:
            print(f"{args.pack}: a parte gerada está desatualizada; rode o gerador", file=sys.stderr)
            return 1
        return 0
    if novo != atual:
        args.pack.write_text(novo, encoding="utf-8", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
