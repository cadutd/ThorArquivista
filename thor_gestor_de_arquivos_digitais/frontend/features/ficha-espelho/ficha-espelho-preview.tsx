"use client";

import type { CSSProperties } from "react";
import {
  campoFichaEspelhoLabels,
  type CampoFichaEspelho,
  type FichaEspelhoDados,
  type ModeloFichaEspelho,
  type ModeloFichaEspelhoPayload,
} from "@/types/ficha-espelho";

type PreviewModelo = Pick<
  ModeloFichaEspelho | ModeloFichaEspelhoPayload,
  "campos" | "tamanho_papel" | "orientacao" | "colunas" | "largura_cm" | "altura_cm"
>;

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

export const sampleFichaEspelhoData: FichaEspelhoDados = {
  unidade_id: 0,
  unidade_produtora: "Secretaria de Administração",
  fundo: "Arquivo Institucional",
  classe: "Gestão documental",
  subclasse: "Processos administrativos",
  descricao_conteudo: "Processos, relatórios e documentos administrativos acondicionados na unidade.",
  data_limite: "1998-2004",
  identificador_caixa: "CX-ARQ-0001",
  codigo_barras: "CX-ARQ-0001",
};

export function getPageGeometry(size: "A4" | "CARTA", orientation: "RETRATO" | "PAISAGEM") {
  const base = size === "CARTA" ? { widthCm: 21.59, heightCm: 27.94 } : { widthCm: 21, heightCm: 29.7 };
  return orientation === "PAISAGEM" ? { widthCm: base.heightCm, heightCm: base.widthCm } : base;
}

export function getFichaLayout(modelo: PreviewModelo) {
  const page = getPageGeometry(modelo.tamanho_papel, modelo.orientacao);
  const printableWidth = page.widthCm - 2.4;
  const printableHeight = page.heightCm - 2.4;
  const modelColumns = Math.max(1, Math.min(modelo.colunas || 1, 2));
  const maxWidthPerColumn = (printableWidth - 0.2 * Math.max(0, modelColumns - 1)) / modelColumns;
  const effectiveWidth = roundCm(Math.min(modelo.largura_cm || maxWidthPerColumn, maxWidthPerColumn));
  const effectiveHeight = roundCm(Math.min(modelo.altura_cm || printableHeight, printableHeight));
  const columns = Math.max(1, Math.min(modelColumns, Math.floor((printableWidth + 0.2) / (effectiveWidth + 0.2)) || 1));
  const rows = Math.max(1, Math.floor((printableHeight + 0.2) / (effectiveHeight + 0.2)) || 1);

  return {
    page,
    printableWidth,
    printableHeight,
    effectiveWidth,
    effectiveHeight,
    columns,
    rows,
    fichasPerPage: Math.max(1, columns * rows),
  };
}

export function FichaEspelhoPreview({
  modelo,
  data = sampleFichaEspelhoData,
  logo,
  institutionName = "Instituição",
}: {
  modelo: PreviewModelo;
  data?: FichaEspelhoDados;
  logo?: string | null;
  institutionName?: string | null;
}) {
  const layout = getFichaLayout(modelo);
  const pageScale = modelo.orientacao === "PAISAGEM" ? 0.42 : 0.5;

  return (
    <div className="space-y-3">
      <div className="overflow-auto rounded-md border bg-muted/30 p-3">
        <div
          className="mx-auto"
          style={{
            width: `${layout.page.widthCm * pageScale}cm`,
            height: `${layout.page.heightCm * pageScale}cm`,
          }}
        >
          <section
            className="bg-white p-3 shadow-sm"
            style={{
              width: `${layout.page.widthCm}cm`,
              minHeight: `${layout.page.heightCm}cm`,
              transform: `scale(${pageScale})`,
              transformOrigin: "top left",
            }}
          >
            <div
              className="grid"
              style={{
                gridTemplateColumns: `repeat(${layout.columns}, ${layout.effectiveWidth}cm)`,
                gridAutoRows: `${layout.effectiveHeight}cm`,
                gap: "0.2cm",
                alignContent: "start",
                justifyContent: "start",
              }}
            >
              {Array.from({ length: Math.min(layout.fichasPerPage, 4) }).map((_, index) => (
                <article
                  key={index}
                  className="bg-white text-black"
                  style={{
                    width: `${layout.effectiveWidth}cm`,
                    height: `${layout.effectiveHeight}cm`,
                    overflow: "hidden",
                  }}
                >
                  <FichaEspelho data={data} fields={modelo.campos} logo={logo} institutionName={institutionName} />
                </article>
              ))}
            </div>
          </section>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">
        Prévia em escala. Impressão: {layout.effectiveWidth} cm x {layout.effectiveHeight} cm, {layout.columns} coluna(s), até {layout.fichasPerPage} ficha(s) por página.
      </p>
    </div>
  );
}

export function FichaEspelho({
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
        {hasLogo ? (
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

        {hasBarcode ? <Barcode value={data.codigo_barras || data.identificador_caixa} /> : null}
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

function roundCm(value: number) {
  return Math.floor(value * 10) / 10;
}
