import "./globals.css";

export const metadata = {
  title: "Thor Pesquisador",
  description: "Instrumentos de pesquisa dinamicos"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
