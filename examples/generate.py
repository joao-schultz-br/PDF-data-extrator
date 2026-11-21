"""Gera dois PDFs de demonstração com conteúdo fictício."""

from pathlib import Path

import pymupdf

EXAMPLES = {
    "ordem-ficticia.pdf": [
        "ORDEM DE SERVIÇO",
        "Cliente: Empresa Exemplo",
        "Data: 15/03/2026",
        "Serviço: Revisão de equipamento",
        "Valor: R$ 1.250,00",
        "Situação: Pendente",
    ],
    "outro-modelo.pdf": [
        "RELATÓRIO DE DEMONSTRAÇÃO",
        "Este documento contém texto fictício em outro formato.",
    ],
}


def main() -> None:
    for filename, lines in EXAMPLES.items():
        with pymupdf.open() as pdf:
            page = pdf.new_page()
            page.insert_text((72, 72), "\n".join(lines), fontsize=12)
            pdf.save(Path(__file__).parent / filename)


if __name__ == "__main__":
    main()
