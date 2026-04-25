export const tipoLocalOptions = [
  ["DEPOSITO", "Depósito"],
  ["SALA_COFRE", "Sala-cofre"],
  ["DATA_CENTER", "Data center"],
  ["MAPOTECA", "Mapoteca"],
  ["LABORATORIO", "Laboratório"],
  ["NUVEM", "Nuvem"],
  ["OUTRO", "Outro"],
] as const;

export const tipoZonaOptions = [
  ["ACERVO_TEXTUAL", "Acervo textual"],
  ["CARTOGRAFICO", "Cartográfico"],
  ["ICONOGRAFICO", "Iconográfico"],
  ["MIDIAS_REMOVIVEIS", "Mídias removíveis"],
  ["FITAS_LTO", "Fitas LTO"],
  ["STORAGE_ONLINE", "Storage online"],
  ["QUARENTENA", "Quarentena"],
  ["BACKUP", "Backup"],
  ["ACESSO", "Acesso"],
  ["OUTRO", "Outro"],
] as const;

export const tipoEstruturaOptions = [
  ["ESTANTE", "Estante"],
  ["ARQUIVO_DESLIZANTE", "Arquivo deslizante"],
  ["MAPOTECA", "Mapoteca"],
  ["GAVETEIRO", "Gaveteiro"],
  ["ARMARIO", "Armário"],
  ["RACK", "Rack"],
  ["COFRE", "Cofre"],
  ["SERVIDOR", "Servidor"],
  ["NAS", "NAS"],
  ["BUCKET_S3", "Bucket S3"],
  ["VOLUME_REDE", "Volume de rede"],
  ["UNIDADE_LTO", "Unidade LTO"],
  ["OUTRO", "Outro"],
] as const;

export const tipoCompartimentoOptions = [
  ["PRATELEIRA", "Prateleira"],
  ["GAVETA", "Gaveta"],
  ["BANDEJA", "Bandeja"],
  ["SLOT", "Slot"],
  ["VOLUME", "Volume"],
  ["DIRETORIO", "Diretório"],
  ["BUCKET", "Bucket"],
  ["PARTICAO", "Partição"],
  ["CAIXA_INTERNA", "Caixa interna"],
  ["OUTRO", "Outro"],
] as const;

export const tipoPosicaoOptions = [
  ["POSICAO_CAIXA", "Posição de caixa"],
  ["POSICAO_PASTA", "Posição de pasta"],
  ["POSICAO_VOLUME", "Posição de volume"],
  ["POSICAO_MAPA", "Posição de mapa"],
  ["SLOT_FITA", "Slot de fita"],
  ["SLOT_MIDIA", "Slot de mídia"],
  ["DIRETORIO_AIP", "Diretório AIP"],
  ["DIRETORIO_SIP", "Diretório SIP"],
  ["DIRETORIO_DIP", "Diretório DIP"],
  ["BUCKET_OBJETO", "Objeto em bucket"],
  ["VOLUME_LOGICO", "Volume lógico"],
  ["OUTRO", "Outro"],
] as const;

const labels = new Map<string, string>([
  ...tipoLocalOptions,
  ...tipoZonaOptions,
  ...tipoEstruturaOptions,
  ...tipoCompartimentoOptions,
  ...tipoPosicaoOptions,
]);

export function storageLabel(value?: string | null) {
  if (!value) {
    return "-";
  }

  return labels.get(value) ?? value;
}
