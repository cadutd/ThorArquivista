import { Badge } from "@/components/ui/badge";

type Props = {
  value: string;
};

export function StatusBadge({ value }: Props) {
  const normalized = value.toUpperCase();
  const variant =
    normalized === "ATIVA" || normalized === "ATIVO" || normalized.includes("SUCESSO")
      ? "success"
      : normalized.includes("ALERTA") || normalized.includes("VERIFICACAO")
        ? "warning"
        : normalized.includes("FALHA") || normalized.includes("CORROMPIDA")
          ? "danger"
          : "neutral";

  return <Badge variant={variant}>{value.replaceAll("_", " ")}</Badge>;
}
