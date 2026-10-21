export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toUpperCase();
  const variant = ["ATIVA", "ATIVO"].includes(normalized) || normalized.includes("SUCESSO") ? "success" :
    normalized.includes("ALERTA") || normalized.includes("VERIFICACAO") ? "warning" :
    normalized.includes("FALHA") || normalized.includes("CORROMPIDA") ? "danger" : "neutral";
  return <span className={"status-badge status-" + variant}>{value.replaceAll("_", " ")}</span>;
}
