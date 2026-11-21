import re
from datetime import date
from decimal import Decimal
from typing import Optional

import pymupdf

from app.core.limits import MAX_PAGES, MAX_TEXT_CHARS
from app.schemas.documents import DocumentResult, ServiceRecord

SERVICE_TEMPLATE = re.compile(
    r"ORDEM DE SERVIÇO\n"
    r"Cliente: (?P<cliente>[^\n]+)\n"
    r"Data: (?P<data>[0-9]{2}/[0-9]{2}/[0-9]{4})\n"
    r"Serviço: (?P<servico>[^\n]+)\n"
    r"Valor: R\$ (?P<valor>(?:[0-9]{1,3}(?:\.[0-9]{3}){1,4}|[0-9]{1,15}),[0-9]{2})\n"
    r"Situação: (?P<situacao>Pago|Pendente|Cancelado)"
)


class DocumentError(ValueError):
    pass


def read_pdf(data: bytes) -> str:
    if not data.startswith(b"%PDF-"):
        raise DocumentError("O arquivo não tem uma assinatura PDF válida.")

    try:
        with pymupdf.open(stream=data, filetype="pdf") as document:
            if not document.is_pdf or document.is_repaired:
                raise DocumentError("O PDF está inválido ou corrompido.")
            if document.needs_pass or document.is_encrypted:
                raise DocumentError("O PDF está protegido por senha.")
            if document.page_count > MAX_PAGES:
                raise DocumentError(f"O PDF excede o limite de {MAX_PAGES} páginas.")

            pages = []
            text_length = 0
            for page in document:
                page_text = page.get_text(sort=True).strip()
                if not pages and not page_text:
                    continue
                text_length += len(page_text) + bool(pages)
                if page_text and text_length > MAX_TEXT_CHARS:
                    raise DocumentError("O PDF excede o limite de texto extraído.")
                pages.append(page_text)
    except DocumentError:
        raise
    except (RuntimeError, ValueError) as exc:
        raise DocumentError("Não foi possível ler o PDF.") from exc

    text = "\n".join(pages).strip()
    if not text:
        raise DocumentError("O PDF não contém texto selecionável.")
    return text


def parse_service_record(text: str) -> Optional[ServiceRecord]:
    lines = (line.strip() for line in text.splitlines())
    match = SERVICE_TEMPLATE.fullmatch("\n".join(line for line in lines if line))
    if not match:
        return None

    day, month, year = map(int, match["data"].split("/"))
    try:
        service_date = date(year, month, day)
    except ValueError:
        return None

    amount = Decimal(match["valor"].replace(".", "").replace(",", "."))
    return ServiceRecord(
        cliente=match["cliente"],
        data=service_date.isoformat(),
        servico=match["servico"],
        valor=str(amount),
        situacao=match["situacao"],
    )


def extract_document(filename: str, data: bytes) -> DocumentResult:
    try:
        text = read_pdf(data)
    except DocumentError as exc:
        return DocumentResult(filename=filename, status="error", message=str(exc))

    record = parse_service_record(text)
    if record is None:
        return DocumentResult(
            filename=filename,
            status="unrecognized",
            text=text,
            message="O texto foi extraído, mas a ordem de serviço não corresponde ao modelo.",
        )
    return DocumentResult(filename=filename, status="extracted", text=text, record=record)
