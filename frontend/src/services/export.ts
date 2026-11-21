import type { DocumentResult } from "../types/documents"

function csvCell(value: string): string {
  // Impede que planilhas interpretem dados do PDF como fórmulas.
  const safe = /^[\s\uFEFF]*[=+\-@＝＋－＠]|^[\t\r\n]/u.test(value) ? "'" + value : value
  return '"' + safe.replaceAll('"', '""') + '"'
}

export function resultsToCsv(results: DocumentResult[]): string {
  const rows = results.map(({ filename, status, record, message, text }) => [
    filename, status, record?.cliente ?? "", record?.data ?? "", record?.servico ?? "",
    record?.valor ?? "", record?.situacao ?? "", message ?? "", text ?? "",
  ])
  const header = ["arquivo", "status", "cliente", "data", "servico", "valor", "situacao", "mensagem", "texto"]
  return [header, ...rows].map((row) => row.map(csvCell).join(",")).join("\r\n") + "\r\n"
}

export function downloadResults(results: DocumentResult[], format: "json" | "csv") {
  const csv = format === "csv"
  const contents = csv ? "\uFEFF" + resultsToCsv(results) : JSON.stringify(results, null, 2)
  const blob = new Blob([contents], { type: csv ? "text/csv;charset=utf-8" : "application/json" })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = "resultados." + format
  link.click()
  window.setTimeout(() => URL.revokeObjectURL(url), 1000)
}
