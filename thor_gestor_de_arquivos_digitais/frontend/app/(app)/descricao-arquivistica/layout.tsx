import Link from "next/link";

const items = [
  ["/descricao-arquivistica", "Edição e Consulta"],
  ["/descricao-arquivistica/unidades", "Associação de Unidades"],
] as const;

export default function DescricaoArquivisticaLayout({
  children,
}: {
  children: React.ReactNode;
}) {
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
