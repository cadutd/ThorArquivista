"use client";

import { useMemo, type CSSProperties } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Printer } from "lucide-react";
import { Button } from "@/components/ui/button";
import { gerarFichasEspelho } from "@/lib/api/ficha-espelho";
import {
  campoFichaEspelhoLabels,
  type CampoFichaEspelho,
  type FichaEspelhoDados,
} from "@/types/ficha-espelho";

const code39: Record<string, string> = {
  "0": "nnnwwnwnn",
  "1": "wnnwnnnnw",
  "2": "nnwwnnnnw",
  "3": "wnwwnnnnn",
  "4": "nnnwwnnnw",
  "5": "wnnwwnnnn",
  "6": "nnwwwnnnn",
  "7": "nnnwnnwnw",
  "8": "wnnwnnwnn",
  "9": "nnwwnnwnn",
  A: "wnnnnwnnw",
  B: "nnwnnwnnw",
  C: "wnwnnwnnn",
  D: "nnnnwwnnw",
  E: "wnnnwwnnn",
  F: "nnwnwwnnn",
  G: "nnnnnwwnw",
  H: "wnnnnwwnn",
  I: "nnwnnwwnn",
  J: "nnnnwwwnn",
  K: "wnnnnnnww",
  L: "nnwnnnnww",
  M: "wnwnnnnwn",
  N: "nnnnwnnww",
  O: "wnnnwnnwn",
  P: "nnwnwnnwn",
  Q: "nnnnnnwww",
  R: "wnnnnnwwn",
  S: "nnwnnnwwn",
  T: "nnnnwnwwn",
  U: "wwnnnnnnw",
  V: "nwwnnnnnw",
  W: "wwwnnnnnn",
  X: "nwnnwnnnw",
  Y: "wwnnwnnnn",
  Z: "nwwnwnnnn",
  "-": "nwnnnnwnw",
  ".": "wwnnnnwnn",
  " ": "nwwnnnwnn",
  $: "nwnwnwnnn",
  "/": "nwnwnnnwn",
  "+": "nwnnnwnwn",
  "%": "nnnwnwnwn",
  "*": "nwnnwnwnn",
};

export default function FichasEspelhoPrintPage() {
  const searchParams = useSearchParams();
  const modeloId = Number(searchParams.get("modeloId"));
  const unidadeIds = useMemo(
    () =>
      (searchParams.get("unidadeIds") ?? "")
        .split(",")
        .map((item) => Number(item))
        .filter((item) => Number.isFinite(item) && item > 0),
    [searchParams],
  );

  const query = useQuery({
    queryKey: ["fichas-espelho", "imprimir", modeloId, unidadeIds],
    queryFn: () => gerarFichasEspelho({ modelo_id: modeloId, unidade_ids: unidadeIds }),
    enabled: Number.isFinite(modeloId) && modeloId > 0 && unidadeIds.length > 0,
  });

  if (!modeloId || !unidadeIds.length) {
    return <p className="text-sm text-destructive">Informe um modelo e ao menos uma unidade para gerar as fichas.</p>;
  }

  if (query.isLoading) {
    return <p className="text-sm text-muted-foreground">Gerando fichas espelho...</p>;
  }

  if (query.error) {
    return <p className="text-sm text-destructive">{query.error.message}</p>;
  }

  const data = query.data;
  if (!data) {
    return null;
  }
  const paperSize = data.modelo.tamanho_papel === "CARTA" ? "letter" : "a4";
  const page = getPageGeometry(data.modelo.tamanho_papel, data.modelo.orientacao);
  const printableWidth = page.widthCm - 2.4;
  const printableHeight = page.heightCm - 2.4;
  const maxWidthPerColumn = (printableWidth - 0.2 * Math.max(0, data.modelo.colunas - 1)) / data.modelo.colunas;
  const effectiveWidth = roundCm(Math.min(data.modelo.largura_cm, maxWidthPerColumn));
  const effectiveHeight = roundCm(Math.min(data.modelo.altura_cm, printableHeight));
  const columns = Math.max(1, Math.min(data.modelo.colunas, Math.floor((printableWidth + 0.2) / (effectiveWidth + 0.2)) || 1));
  const rows = Math.max(1, Math.floor((printableHeight + 0.2) / (effectiveHeight + 0.2)) || 1);
  const fichasPerPage = Math.max(1, columns * rows);
  const pages = chunk(data.fichas, fichasPerPage);

  return (
    <div className="space-y-4">
      <style jsx global>{`
        @media print {
          aside,
          header,
          .print-toolbar {
            display: none !important;
          }

          main {
            max-width: none !important;
            padding: 0 !important;
          }

          body {
            background: white !important;
          }

          .print-grid,
          .print-grid * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }

          .print-grid {
            border-collapse: collapse !important;
            border: 2pt solid #000 !important;
          }

          .print-grid-cell {
            border: 1pt solid #000 !important;
          }

          .print-grid-label {
            background: #f1f1f1 !important;
            box-shadow: inset 0 0 0 1000px #f1f1f1 !important;
          }

          .sheet-grid {
            display: grid;
            grid-template-columns: repeat(${columns}, ${effectiveWidth}cm) !important;
            grid-auto-rows: ${effectiveHeight}cm !important;
            gap: 0.2cm !important;
            align-content: start !important;
            justify-content: start !important;
          }

          .mirror-sheet {
            break-inside: avoid;
            page-break-inside: avoid;
            overflow: hidden !important;
          }

          .print-page {
            width: auto !important;
            min-height: 0 !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            break-after: page;
            page-break-after: always;
          }

          .print-page:last-child {
            break-after: auto;
            page-break-after: auto;
          }

          @page {
            size: ${paperSize} ${data.modelo.orientacao === "PAISAGEM" ? "landscape" : "portrait"};
            margin: 12mm;
          }
        }
      `}</style>
      <div className="print-toolbar flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal">Ficha espelho</h1>
          <p className="text-sm text-muted-foreground">
            {data.fichas.length} ficha(s) usando o modelo {data.modelo.nome}.
          </p>
        </div>
        <Button type="button" onClick={() => window.print()}>
          <Printer className="h-4 w-4" />
          Imprimir
        </Button>
      </div>

      <div className="space-y-6">
        {pages.map((pageItems, pageIndex) => (
          <section
            key={pageIndex}
            className="print-page bg-white p-4 shadow-sm"
            style={{ width: `${page.widthCm}cm`, minHeight: `${page.heightCm}cm` }}
          >
            <div
              className="sheet-grid grid"
              style={{
                gridTemplateColumns: `repeat(${columns}, ${effectiveWidth}cm)`,
                gridAutoRows: `${effectiveHeight}cm`,
                gap: "0.2cm",
                alignContent: "start",
                justifyContent: "start",
              }}
            >
              {pageItems.map((ficha) => (
                <article
                  key={ficha.unidade_id}
                  className="mirror-sheet bg-white p-0 text-black"
                  style={{
                    width: `${effectiveWidth}cm`,
                    height: `${effectiveHeight}cm`,
                    overflow: "hidden",
                  }}
                >
                  <Ficha data={ficha} fields={data.modelo.campos} logo={data.instituicao.logotipo_data_url} institutionName={data.instituicao.nome} />
                </article>
              ))}
            </div>
          </section>
        ))}
      </div>
    </div>
  );
}

function getPageGeometry(size: "A4" | "CARTA", orientation: "RETRATO" | "PAISAGEM") {
  const base = size === "CARTA" ? { widthCm: 21.59, heightCm: 27.94 } : { widthCm: 21, heightCm: 29.7 };
  return orientation === "PAISAGEM" ? { widthCm: base.heightCm, heightCm: base.widthCm } : base;
}

function chunk<T>(items: T[], size: number) {
  const pages: T[][] = [];
  for (let index = 0; index < items.length; index += size) {
    pages.push(items.slice(index, index + size));
  }
  return pages;
}

function roundCm(value: number) {
  return Math.floor(value * 10) / 10;
}

function Ficha({
  data,
  fields,
  logo,
  institutionName,
}: {
  data: FichaEspelhoDados;
  fields: CampoFichaEspelho[];
  logo?: string | null;
  institutionName?: string | null;
}) {
  const visibleMetadataFields = fields.filter((field) => field !== "logo_instituicao" && field !== "codigo_barras");
  const hasLogo = fields.includes("logo_instituicao");
  const hasBarcode = fields.includes("codigo_barras");
  const fixedRows = (hasLogo ? 2.2 : 0) + (hasBarcode ? 1.8 : 0);
  const metadataRowHeight = `calc((100% - ${fixedRows}cm) / ${Math.max(1, visibleMetadataFields.length)})`;

  return (
    <table
      className="print-grid h-full w-full text-black"
      style={{
        borderCollapse: "collapse",
        border: "2pt solid #000",
        tableLayout: "fixed",
        height: "100%",
        maxHeight: "100%",
        overflow: "hidden",
      }}
    >
      <tbody>
      {fields.includes("logo_instituicao") ? (
        <tr style={{ height: "2.2cm" }}>
          <td className="print-grid-cell" colSpan={2} style={gridCellStyle}>
            <div className="flex h-full min-h-0 items-center justify-center overflow-hidden">
              {logo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={logo}
                  alt={institutionName ?? "Logotipo da instituição"}
                  style={{
                    width: "5cm",
                    height: "1.5cm",
                    objectFit: "contain",
                  }}
                />
              ) : (
                <div className="text-center text-sm font-semibold">{institutionName ?? "Instituição"}</div>
              )}
            </div>
          </td>
        </tr>
      ) : null}

      {visibleMetadataFields.map((field) => (
          <FichaField
            key={field}
            label={campoFichaEspelhoLabels[field]}
            value={fieldValue(data, field)}
            featured={field === "identificador_caixa"}
            rowHeight={metadataRowHeight}
          />
        ))}

      {fields.includes("codigo_barras") ? <Barcode value={data.codigo_barras || data.identificador_caixa} /> : null}
      </tbody>
    </table>
  );
}

function FichaField({
  label,
  value,
  featured,
  rowHeight,
}: {
  label: string;
  value?: string | null;
  featured?: boolean;
  rowHeight: string;
}) {
  return (
    <tr style={{ height: rowHeight }}>
      <td
        className="print-grid-cell print-grid-label"
        style={{
          ...gridCellStyle,
          width: "34%",
          verticalAlign: "top",
          background: "#f1f1f1",
          boxShadow: "inset 0 0 0 1000px #f1f1f1",
          overflow: "hidden",
        }}
      >
        <div className="overflow-hidden text-[9px] font-bold uppercase leading-tight">{label}</div>
      </td>
      <td className="print-grid-cell" style={{ ...gridCellStyle, verticalAlign: "top", overflow: "hidden" }}>
        <div className={featured ? "overflow-hidden text-lg font-bold leading-tight" : "overflow-hidden text-xs leading-tight"}>{value || "-"}</div>
      </td>
    </tr>
  );
}

function Barcode({ value }: { value: string }) {
  const normalized = normalizeCode39(value);
  const pattern = `*${normalized}*`;
  return (
    <tr style={{ height: "1.8cm" }}>
      <td className="print-grid-cell" colSpan={2} style={gridCellStyle}>
        <div className="mx-auto flex h-6 w-full max-w-xl items-end justify-center overflow-hidden bg-white">
          {pattern.split("").map((char, index) => (
            <BarcodeChar key={`${char}-${index}`} char={char} />
          ))}
        </div>
        <div className="mt-0.5 overflow-hidden text-center font-mono text-[10px] tracking-normal">{normalized}</div>
      </td>
    </tr>
  );
}

const gridCellStyle: CSSProperties = {
  border: "1pt solid #000",
  padding: "4px 6px",
};

function BarcodeChar({ char }: { char: string }) {
  const pattern = code39[char] ?? code39["-"];
  const bars = pattern.split("");
  return (
    <span className="flex h-full items-end">
      {bars.map((width, index) => (
        <span
          key={index}
          className={index % 2 === 0 ? "h-full bg-black" : "h-full bg-white"}
          style={{ width: width === "w" ? 3 : 1 }}
        />
      ))}
      <span className="h-full w-px bg-white" />
    </span>
  );
}

function normalizeCode39(value: string) {
  return value
    .toUpperCase()
    .split("")
    .map((char) => (code39[char] && char !== "*" ? char : "-"))
    .join("");
}

function fieldValue(data: FichaEspelhoDados, field: CampoFichaEspelho) {
  switch (field) {
    case "unidade_produtora":
      return data.unidade_produtora;
    case "fundo":
      return data.fundo;
    case "classe":
      return data.classe;
    case "subclasse":
      return data.subclasse;
    case "descricao_conteudo":
      return data.descricao_conteudo;
    case "data_limite":
      return data.data_limite;
    case "identificador_caixa":
      return data.identificador_caixa;
    case "codigo_barras":
      return data.codigo_barras;
    case "logo_instituicao":
      return null;
  }
}
