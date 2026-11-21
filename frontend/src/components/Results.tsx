import { downloadResults } from "../services/export"
import type { DocumentResult } from "../types/documents"

const statusLabel = {
  extracted: "Dados extraídos",
  unrecognized: "Somente texto",
  error: "Erro",
}

function formatAmount(amount: string): string {
  const [whole, cents] = amount.split(".")
  return "R$ " + BigInt(whole).toLocaleString("pt-BR") + "," + cents
}

export function Results({ results }: { results: DocumentResult[] }) {
  return (
    <section aria-labelledby="results-title">
      <div className="section-heading">
        <h2 id="results-title">Resultados</h2>
        <div className="actions">
          <button type="button" onClick={() => downloadResults(results, "json")}>Baixar JSON</button>
          <button type="button" onClick={() => downloadResults(results, "csv")}>Baixar CSV</button>
        </div>
      </div>
      {results.map(({ filename, status, record, message, text }, index) => (
        <article key={index}>
          <span className={"file-status " + status}>{statusLabel[status]}</span>
          <h3>{filename}</h3>
          {message && <p>{message}</p>}
          {record && (
            <dl>
              <div><dt>Cliente</dt><dd>{record.cliente}</dd></div>
              <div><dt>Data</dt><dd>{record.data.split("-").reverse().join("/")}</dd></div>
              <div><dt>Serviço</dt><dd>{record.servico}</dd></div>
              <div><dt>Valor</dt><dd>{formatAmount(record.valor)}</dd></div>
              <div><dt>Situação</dt><dd>{record.situacao}</dd></div>
            </dl>
          )}
          {text && <details open={status === "unrecognized"}><summary>Texto extraído</summary><pre>{text}</pre></details>}
        </article>
      ))}
    </section>
  )
}
