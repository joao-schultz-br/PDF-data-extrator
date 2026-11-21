from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.api.routes import documents
from app.main import app
from app.services import documents as extraction

EXAMPLES = Path(__file__).resolve().parents[2] / "examples"
EXTRACT = "/api/documents/extract"


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_mixed_batch_preserves_order_and_partial_results(client):
    response = client.post(
        EXTRACT,
        files=[
            ("files", (name, (EXAMPLES / name).read_bytes(), "application/pdf"))
            for name in ("ordem-ficticia.pdf", "outro-modelo.pdf")
        ] + [("files", ("invalido.pdf", b"texto", "application/pdf"))],
    )
    assert response.status_code == 200
    known, unknown, invalid = response.json()["results"]
    assert known["status"] == "extracted"
    assert known["record"] == {
        "cliente": "Empresa Exemplo",
        "data": "2026-03-15",
        "servico": "Revisão de equipamento",
        "valor": "1250.00",
        "situacao": "Pendente",
    }
    assert unknown["status"] == "unrecognized"
    assert "RELATÓRIO" in unknown["text"]
    assert unknown["record"] is None
    assert invalid["status"] == "error"
    assert invalid["message"]


def test_rejects_oversized_file_without_discarding_batch(client):
    response = client.post(EXTRACT, files=[
        ("files", ("grande.pdf", b"x" * (documents.MAX_FILE_BYTES + 1))),
        ("files", ("ordem.pdf", (EXAMPLES / "ordem-ficticia.pdf").read_bytes())),
    ])
    assert response.status_code == 200
    too_big, valid = response.json()["results"]
    assert too_big["message"] == "O PDF excede 10 MB."
    assert valid["status"] == "extracted"


def test_rejects_too_many_files(client):
    response = client.post(EXTRACT, files=[("files", ("x.pdf", b"x"))] * 11)
    assert response.status_code == 400


def test_rejects_batch_over_request_limit(client, monkeypatch):
    monkeypatch.setattr(documents, "MAX_REQUEST_BYTES", 1000)
    response = client.post(EXTRACT, files={"files": ("x.pdf", b"x" * 1000)})
    assert response.status_code == 413


def test_rejects_wrong_media_type_and_field(client):
    assert client.post(EXTRACT, json={}).status_code == 415
    assert client.post(EXTRACT, files={"pdf": ("x.pdf", b"x")}).status_code == 400


def test_rejects_truncated_multipart(client):
    response = client.post(
        EXTRACT,
        content=b'--abc\r\nContent-Disposition: form-data; name="files"; filename="x.pdf"\r\n\r\nx',
        headers={"Content-Type": "multipart/form-data; boundary=abc"},
    )
    assert response.status_code == 400


def test_text_limit_counts_only_returned_text(monkeypatch):
    with pymupdf.open() as pdf:
        pdf.new_page()
        pdf.new_page().insert_text((72, 72), "teste")
        pdf.new_page()
        data = pdf.tobytes()

    monkeypatch.setattr(extraction, "MAX_TEXT_CHARS", 5)
    assert extraction.read_pdf(data) == "teste"

    monkeypatch.setattr(extraction, "MAX_TEXT_CHARS", 4)
    with pytest.raises(extraction.DocumentError, match="limite de texto"):
        extraction.read_pdf(data)


@pytest.mark.parametrize("encrypted", [True, False])
def test_reports_encrypted_and_textless_pdfs(client, encrypted):
    with pymupdf.open() as pdf:
        pdf.new_page()
        options = {"encryption": pymupdf.PDF_ENCRYPT_AES_256, "user_pw": "example"} if encrypted else {}
        data = pdf.tobytes(**options)

    response = client.post(EXTRACT, files={"files": ("documento.pdf", data)})
    assert response.status_code == 200
    result, = response.json()["results"]
    assert result["status"] == "error"
    assert ("senha" if encrypted else "texto selecionável") in result["message"]
