from asyncio import get_running_loop
from collections.abc import AsyncIterator
from concurrent.futures.process import BrokenProcessPool

from fastapi import APIRouter, HTTPException, Request
from python_multipart.exceptions import MultipartParseError
from starlette.datastructures import FormData, UploadFile
from starlette.formparsers import MultiPartException, MultiPartParser
from starlette.requests import ClientDisconnect

from app.core.limits import MAX_FILE_BYTES, MAX_FILES, MAX_REQUEST_BYTES
from app.schemas.documents import DocumentResult, ExtractionResponse
from app.services.documents import extract_document

router = APIRouter(prefix="/api/documents", tags=["Documentos"])


class RequestTooLarge(MultiPartException):
    pass


class UploadParser(MultiPartParser):
    complete = False

    def on_end(self) -> None:
        self.complete = True

    async def parse(self) -> FormData:
        try:
            form = await super().parse()
            if not self.complete:
                raise MultiPartException("O envio multipart está incompleto.")
            return form
        except BaseException:
            # Starlette fecha os temporários apenas em MultiPartException.
            for file in self._files_to_close_on_error:
                file.close()
            raise


async def limited_body(request: Request) -> AsyncIterator[bytes]:
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_REQUEST_BYTES:
            raise RequestTooLarge("O lote excede o limite de tamanho da solicitação.")
        yield chunk


@router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="Extrai texto e dados de até 10 PDFs",
    responses={
        400: {"description": "Lote inválido"},
        413: {"description": "Solicitação muito grande"},
        415: {"description": "Tipo de solicitação incompatível"},
        503: {"description": "Processo de extração indisponível"},
    },
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["files"],
                        "properties": {
                            "files": {
                                "type": "array",
                                "items": {"type": "string", "format": "binary"},
                                "minItems": 1,
                                "maxItems": MAX_FILES,
                            }
                        },
                    }
                }
            },
        }
    },
)
async def extract_documents(request: Request) -> ExtractionResponse:
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip()
    if content_type.lower() != "multipart/form-data":
        raise HTTPException(415, "Envie os PDFs como multipart/form-data.")

    parser = UploadParser(
        request.headers, limited_body(request), max_files=MAX_FILES, max_fields=0
    )
    try:
        form = await parser.parse()
    except RequestTooLarge as exc:
        raise HTTPException(413, exc.message) from exc
    except (MultiPartException, MultipartParseError, ClientDisconnect) as exc:
        raise HTTPException(400, f"Envie de 1 a {MAX_FILES} PDFs no campo files.") from exc

    try:
        files = form.multi_items()
        if not files or any(name != "files" for name, _ in files):
            raise HTTPException(400, "Envie os PDFs no campo files.")

        results = []
        for _, file in files:
            if not isinstance(file, UploadFile):
                raise HTTPException(400, "O campo files aceita somente arquivos.")

            filename = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
            filename = filename[:255] or "Arquivo sem nome"
            data = (
                await file.read(MAX_FILE_BYTES + 1)
                if file.size is None or file.size <= MAX_FILE_BYTES
                else None
            )
            if data is None or len(data) > MAX_FILE_BYTES:
                results.append(
                    DocumentResult(
                        filename=filename, status="error", message="O PDF excede 10 MB."
                    )
                )
                continue

            try:
                result = await get_running_loop().run_in_executor(
                    request.app.state.pdf_executor, extract_document, filename, data
                )
            except BrokenProcessPool as exc:
                raise HTTPException(503, "Processo de extração indisponível.") from exc
            results.append(result)
        return ExtractionResponse(results=results)
    finally:
        await form.close()
