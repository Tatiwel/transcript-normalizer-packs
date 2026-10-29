"""Gera os termos de ações do financas-ptbr a partir de fontes/acoes.csv.

    uv run --project ../transcript-normalizer python financas-ptbr/tools/gerar_termos.py [--relatorio] [--verificar]

Lê só as linhas com `status=conferido` e `usar_no_pack=sim` e escreve um termo por
empresa num bloco delimitado do `pack.yaml`. Rodar de novo substitui só esse bloco;
o resto do arquivo fica idêntico, byte a byte. Determinístico e sem rede: a mesma
entrada dá sempre o mesmo arquivo. Dobra o texto com o módulo pt-BR da engine
(D-033), o mesmo que o matcher usa, por isso roda no ambiente da engine.

As regras, cada uma pela decisão da engine que a pede:

- Um termo por empresa, classe `companhia`, canônico igual à coluna `nome`, com
  `match: exact` (D-090): casa só por igualdade com as próprias formas, sem fuzzy, sem
  regra fonética, sem flexão e sem número por extenso. Os erros de cada empresa entram
  depois, como variantes vindas de vídeos reais.
- Tickers (atuais e antigos) e apelidos entram como aliases, reconhecidos e nunca
  substituídos (D-020). Um nome antigo dito no vídeo ("Eletrobras", ELET3) fica como foi dito.
- Uma forma com mais de 3 palavras nunca casa: o matcher compara janelas de até 3
  (NGRAM_SIZES). Um apelido assim é descartado, e uma empresa cujo nome tem mais de 3
  palavras não é gerada.
- O curado ganha: uma empresa com nome, apelido ou ticker igual a uma forma de um
  termo curado, ou cujo nome contém o nome de uma companhia curada, não é gerada.
  Uma forma gerada igual a uma forma curada, ou à de outra empresa gerada, é descartada.
- Palavra comum (D-032, D-086), pela lista `palavras_comuns.txt`: um nome com
  `palavra_comum=sim` ou feito só de palavras comuns ganha `context:` com termos curados
  de mercado de ações. Um apelido não pode ter contexto (D-086): um apelido de uma
  palavra só que seja comum é descartado, e a lista exclui algumas formas inteiras.
- Caixa (D-090, `case_sensitive`): um nome de até 4 letras, um nome de uma palavra só
  com contexto e um apelido de até 4 letras sem dígito só casam escritos como no CSV.
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

from transcript_normalizer.core.matcher import NGRAM_SIZES, tokenize
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
#: Nomes e apelidos de até tantas letras só casam na caixa em que estão escritos.
CURTO = 4
#: O matcher compara janelas de até tantas palavras (matcher.NGRAM_SIZES).
MAX_PALAVRAS = max(NGRAM_SIZES)
#: Como começa o motivo de uma forma descartada por ser igual a outra.
COLISAO = "colisão, igual a "
#: Como começa o motivo de uma forma longa demais para o matcher.
LONGO = f"mais de {MAX_PALAVRAS} palavras"


def dobra(texto: str) -> str:
    """Como a engine compara um termo de `match: exact`: o `fold` do idioma (D-090)."""
    return getattr(pt_br, "fold", pt_br.normalize)(texto)


def palavras_de(texto: str) -> int:
    """Quantas palavras o matcher vê na forma (D-024: suas janelas são de palavras)."""
    return len(tokenize(texto, pt_br.sentence_boundaries))


def letras(dobrado: str) -> int:
    return len(dobrado.replace(" ", ""))


def ler_palavras(texto: str) -> tuple[frozenset[str], frozenset[str]]:
    """(palavras comuns, formas excluídas): uma por linha; `= forma` exclui a forma inteira."""
    palavras, excluidas = set(), set()
    for linha in texto.splitlines():
        linha = linha.split("#", 1)[0].strip()
        if linha.startswith("="):
            excluidas.add(dobra(linha[1:].strip()))
        elif linha:
            palavras.add(dobra(linha))
    return frozenset(palavras), frozenset(excluidas)


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
    caixa: list[str] = field(default_factory=list)  # formas que só casam escritas assim


@dataclass
class Relatorio:
    gerados: list[Gerado] = field(default_factory=list)
    pulados: list[tuple[str, str]] = field(default_factory=list)  # (empresa, por quê)
    descartadas: list[tuple[str, str, str]] = field(default_factory=list)  # (empresa, forma, motivo)

    @property
    def protegidos(self) -> list[Gerado]:
        return [g for g in self.gerados if g.protecao]

    def por_motivo(self) -> dict[str, int]:
        contagem: dict[str, int] = {}
        for _, _, motivo in self.descartadas:
            chave = next((m for m in (COLISAO, LONGO) if motivo.startswith(m)), motivo.split(":", 1)[0])
            chave = chave.rstrip(", ").removesuffix(", igual a")
            contagem[chave] = contagem.get(chave, 0) + 1
        return dict(sorted(contagem.items()))

    def resumo(self) -> str:
        curadas = sum(1 for _, motivo in self.pulados if not motivo.startswith(LONGO))
        out = [
            f"termos gerados: {len(self.gerados)}",
            f"empresas puladas por já serem curadas: {curadas}",
            f"empresas puladas por nome com mais de {MAX_PALAVRAS} palavras: {len(self.pulados) - curadas}",
            f"nomes com contexto: {len(self.protegidos)}",
            f"termos com formas de caixa exata: {sum(1 for g in self.gerados if g.caixa)}",
            f"formas descartadas: {len(self.descartadas)}",
        ]
        out += [f"  {motivo}: {n}" for motivo, n in self.por_motivo().items()]
        return "\n".join(out)

    def completo(self) -> str:
        out = [self.resumo(), "", f"contexto de todos os nomes com contexto: {', '.join(CONTEXTO)}", ""]
        out.append("empresas puladas:")
        out += [f"  {nome}: {motivo}" for nome, motivo in self.pulados]
        out += ["", "nomes com contexto:"]
        out += [f"  {g.nome}: {'; '.join(g.protecao)}" for g in self.protegidos]
        out += ["", "formas de caixa exata (case_sensitive):"]
        out += [f"  {g.nome}: {', '.join(g.caixa)}" for g in self.gerados if g.caixa]
        out += ["", "formas descartadas:"]
        out += [f"  {nome}: {forma!r} ({motivo})" for nome, forma, motivo in self.descartadas]
        return "\n".join(out)


def _curados(texto: str) -> list[dict]:
    return (yaml.safe_load(sem_bloco(texto)) or {}).get("terms") or []


def gerar(pack: str, acoes: str, palavras_texto: str) -> tuple[str, Relatorio]:
    """O novo texto do pack.yaml e o que foi feito."""
    palavras, excluidas = ler_palavras(palavras_texto)
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
        if palavras_de(e.nome) > MAX_PALAVRAS:
            relatorio.pulados.append((e.nome, f"{LONGO}: {palavras_de(e.nome)}; o nome nunca casaria"))
            continue

        vistos = {nome}
        aliases, caixa = [], []
        for forma, ticker in [(a, False) for a in e.apelidos] + [(t, True) for t in e.tickers + e.antigos]:
            d = dobra(forma)
            if d in vistos:
                continue
            vistos.add(d)
            if palavras_de(forma) > MAX_PALAVRAS:
                relatorio.descartadas.append((e.nome, forma, f"{LONGO}: {palavras_de(forma)}"))
            elif not ticker and d in excluidas:
                relatorio.descartadas.append((e.nome, forma, "excluída em palavras_comuns.txt"))
            elif not ticker and " " not in d and comum(d, palavras):
                relatorio.descartadas.append((e.nome, forma, "apelido de uma palavra comum: alias não aceita contexto"))
            else:
                aliases.append(forma)
                if not ticker and letras(d) <= CURTO and not any(c.isdigit() for c in d):
                    caixa.append(forma)

        protecao = []
        if e.palavra_comum:
            protecao.append("palavra_comum=sim")
        if comum(nome, palavras):
            protecao.append("palavra comum")
        if letras(nome) <= CURTO or (protecao and " " not in nome):
            caixa.insert(0, e.nome)
        gerados.append(Gerado(e.nome, aliases, protecao, caixa))

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
        g.caixa = [c for c in g.caixa if c == g.nome or c in mantidos]
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
        linhas.append(f"    match: exact\n")
        if g.aliases:
            linhas.append(f"    aliases: [{', '.join(_escalar(a, 'k: [{}]') for a in g.aliases)}]\n")
        if g.protecao:
            linhas.append(f"    context: {{{_escalar(g.nome, '{{{}: x}}')}: [{contexto}]}}\n")
        if g.caixa:
            linhas.append(f"    case_sensitive: [{', '.join(_escalar(c, 'k: [{}]') for c in g.caixa)}]\n")
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
