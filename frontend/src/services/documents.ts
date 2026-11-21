import type { DocumentResult } from "../types/documents"

const apiUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"

export async function extractDocuments(files: File[]): Promise<DocumentResult[]> {
  const body = new FormData()
  for (const file of files) {
    body.append("files", file)
  }

  let response: Response
  try {
    response = await fetch(new URL("/api/documents/extract", apiUrl), {
      method: "POST",
      body,
    })
  } catch {
    throw new Error("Não foi possível conectar à API. Verifique se o backend está em execução.")
  }

  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(
      typeof error?.detail === "string" ? error.detail : "Não foi possível processar o lote.",
    )
  }

  const data: { results?: DocumentResult[] } | null = await response.json().catch(() => null)
  if (!Array.isArray(data?.results) || data.results.length !== files.length) {
    throw new Error("A API retornou um resultado incompleto para o lote.")
  }
  return data.results
}
