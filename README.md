# PDF Data Extractor

Aplicação web para extrair texto selecionável de PDFs e interpretar ordens de serviço de um modelo conhecido. Envie até 10 arquivos, confira o resultado de cada um e baixe o lote em JSON ou CSV.

O frontend usa React, TypeScript e Vite. O backend usa FastAPI e PyMuPDF. Os testes da API usam Pytest.

## Execução local

Use Python 3.9 ou superior, Node.js 22.12 ou superior e npm. Abra dois terminais na raiz do repositório.

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

A documentação interativa está em <http://127.0.0.1:8000/docs>.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

Abra <http://localhost:5173> e selecione os PDFs de demonstração em `examples/`. Clique em **Extrair dados** e use os botões **Baixar JSON** e **Baixar CSV** após o processamento.

Após `npm run build`, use `npm run preview` para abrir a versão compilada em <http://localhost:4173>. A API aceita as origens locais do Vite nas portas 5173 e 4173. Para usar outra API, defina `VITE_API_URL` antes de iniciar o Vite ou compilar o frontend.

## Modelo e resultados

[ordem-ficticia.pdf](examples/ordem-ficticia.pdf) segue o modelo abaixo. [outro-modelo.pdf](examples/outro-modelo.pdf) demonstra o retorno de texto quando a estrutura é diferente. O script [examples/generate.py](examples/generate.py) recria os dois exemplos com o PyMuPDF do ambiente do backend.

```text
ORDEM DE SERVIÇO
Cliente: Empresa Exemplo
Data: 15/03/2026
Serviço: Revisão de equipamento
Valor: R$ 1.250,00
Situação: Pendente
```

A data estruturada segue o formato ISO `AAAA-MM-DD`. O valor em reais é exportado como string decimal para preservar os centavos. As situações aceitas são Pago, Pendente e Cancelado. As exportações incluem texto, dados estruturados e erros por arquivo. O CSV usa vírgulas, UTF-8 com BOM e neutraliza fórmulas em células de texto.

## API

- `GET /api/health` verifica a disponibilidade da API.
- `POST /api/documents/extract` recebe `multipart/form-data` com um campo `files` para cada PDF. O retorno contém `results` na ordem do envio. Cada item tem um status `extracted`, `unrecognized` ou `error`. Um lote válido pode conter sucessos e erros na mesma resposta HTTP 200.
- Lotes inválidos recebem HTTP 400. Um corpo acima de 101 MB, incluindo a estrutura multipart, recebe HTTP 413. Solicitações com outro tipo de conteúdo recebem HTTP 415. Um processo de extração indisponível recebe HTTP 503.

```bash
curl --fail-with-body http://127.0.0.1:8000/api/documents/extract \
  -F 'files=@examples/ordem-ficticia.pdf' \
  -F 'files=@examples/outro-modelo.pdf'
```

Cada PDF pode ter até 10 MB (10.000.000 bytes), 100 páginas e 100 mil caracteres de texto. A API fecha os arquivos temporários após o processamento e retorna um erro por arquivo quando o PDF está corrompido, protegido por senha ou sem texto selecionável.

## Verificação

Com o backend ativo, consulte a rota de saúde.

```bash
curl --fail http://127.0.0.1:8000/api/health
```

Na raiz do repositório, rode os testes da API e compile o frontend.

```bash
(cd backend && .venv/bin/python -m pytest)
(cd frontend && npm run build)
```
