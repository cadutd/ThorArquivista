import "./globals.css";
import { SessionGuard } from "@/components/session-guard";

export const metadata = {
  title: "Thor Pesquisador",
  description: "Instrumentos de pesquisa dinamicos"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body><SessionGuard>{children}</SessionGuard></body>
    </html>
  );
}
