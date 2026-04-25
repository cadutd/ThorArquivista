import Link from "next/link";

const items = [
  ["/enderecamento/locais", "Locais de Guarda"],
  ["/enderecamento/zonas", "Zonas de Guarda"],
  ["/enderecamento/estruturas", "Estruturas"],
  ["/enderecamento/compartimentos", "Compartimentos"],
  ["/enderecamento/posicoes", "Posições"],
  ["/enderecamento/mapa", "Mapa Topográfico"],
  ["/enderecamento/movimentacoes", "Movimentações"],
  ["/enderecamento/ocupacao", "Ocupação"],
] as const;

export default function EnderecamentoLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="space-y-5">
      <nav className="flex gap-2 overflow-x-auto rounded-md border p-2">
        {items.map(([href, label]) => (
          <Link
            key={href}
            href={href}
            className="whitespace-nowrap rounded-md px-3 py-2 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            {label}
          </Link>
        ))}
      </nav>
      {children}
    </div>
  );
}
