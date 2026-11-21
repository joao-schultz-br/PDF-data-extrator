import { useState } from "react"
import type { FormEvent } from "react"
import { Results } from "./components/Results"
import { extractDocuments } from "./services/documents"
import type { DocumentResult } from "./types/documents"

const maxFiles = 10
const maxFileBytes = 10_000_000

export default function App() {
  const [files, setFiles] = useState<File[]>([])
  const [results, setResults] = useState<DocumentResult[]>([])
  const [error, setError] = useState("")
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (busy || !files.length) return

    if (files.length > maxFiles) {
      setError("Selecione até 10 arquivos por vez.")
      return
    }
    setBusy(true)
    setError("")
    setResults([])
    try {
      const validFiles = files.filter((file) => file.size <= maxFileBytes)
      const extracted = validFiles.length ? await extractDocuments(validFiles) : []
      let resultIndex = 0

      setResults(files.map((file) => file.size <= maxFileBytes
        ? extracted[resultIndex++]
        : {
            filename: file.name,
            status: "error",
            record: null,
            text: null,
            message: "O PDF excede 10 MB.",
          },
      ))
    } catch (error) {
      setError(error instanceof Error ? error.message : "Falha ao processar o lote.")
    } finally {
      setBusy(false)
    }
  }

  return (
    <main>
      <header>
        <h1>PDF Data Extractor</h1>
        <p>Extraia texto e dados de ordens de serviço em PDF.</p>
      </header>
      <form onSubmit={submit}>
        <label htmlFor="pdfs">Arquivos PDF</label>
        <p id="limits">Até 10 PDFs por envio, com até 10 MB cada.</p>
        <input
          id="pdfs"
          type="file"
          accept=".pdf,application/pdf"
          multiple
          disabled={busy}
          aria-describedby="limits"
          onChange={(event) => {
            setFiles(Array.from(event.currentTarget.files ?? []))
            setError("")
            setResults([])
          }}
        />
        {files.length > 0 && <ul>{files.map((file, index) => <li key={index}>{file.name}</li>)}</ul>}
        <button type="submit" disabled={busy || !files.length}>Extrair dados</button>
        {error && <p className="error" role="alert">{error}</p>}
      </form>
      <div className="status" role="status">
        {busy && "Processando arquivos…"}
        {results.length === 1 && "1 arquivo processado."}
        {results.length > 1 && `${results.length} arquivos processados.`}
      </div>
      {results.length > 0 && <Results results={results} />}
    </main>
  )
}
