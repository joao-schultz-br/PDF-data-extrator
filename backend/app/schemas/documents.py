from typing import Literal, Optional

from pydantic import BaseModel


class ServiceRecord(BaseModel):
    cliente: str
    data: str
    servico: str
    valor: str
    situacao: Literal["Pago", "Pendente", "Cancelado"]


class DocumentResult(BaseModel):
    filename: str
    status: Literal["extracted", "unrecognized", "error"]
    text: Optional[str] = None
    record: Optional[ServiceRecord] = None
    message: Optional[str] = None


class ExtractionResponse(BaseModel):
    results: list[DocumentResult]
