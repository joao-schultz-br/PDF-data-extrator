export type ServiceRecord = {
  cliente: string
  data: string
  servico: string
  valor: string
  situacao: "Pago" | "Pendente" | "Cancelado"
}

export type DocumentResult = {
  filename: string
  status: "extracted" | "unrecognized" | "error"
  text: string | null
  record: ServiceRecord | null
  message: string | null
}
