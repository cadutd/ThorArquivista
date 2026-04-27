import type { NormaDescricao } from "@/types/descricao-arquivistica";

type HelpEntry = {
  oficial: string;
  finalidade: string;
  regra: string;
  exemplo: string;
};

export const helpTexts: Record<NormaDescricao, Record<string, HelpEntry>> = {
  NOBRADE: {
    codigo_referencia: {
      oficial: "Código de referência",
      finalidade: "Identificar de forma única a unidade de descrição.",
      regra: "Utilizar o padrão institucional definido, evitando duplicidade.",
      exemplo: "BR SPAPESP EDU 001",
    },
    titulo: {
      oficial: "Título",
      finalidade: "Nomear a unidade de descrição.",
      regra: "Registrar título formal ou atribuído, de modo claro e conciso.",
      exemplo: "Fundo Secretaria da Educação",
    },
    nivel: {
      oficial: "Nível de descrição",
      finalidade: "Indicar a posição da unidade na hierarquia arquivística.",
      regra: "Selecionar nível compatível com o registro pai.",
      exemplo: "Nível 3 - Série",
    },
    produtor: {
      oficial: "Nome(s) do(s) produtor(es)",
      finalidade: "Registrar entidade responsável pela acumulação documental.",
      regra: "Informar forma autorizada quando disponível.",
      exemplo: "Secretaria da Educação do Estado de São Paulo",
    },
    condicoes_acesso: {
      oficial: "Condições de acesso",
      finalidade: "Informar restrições ou condições para consulta.",
      regra: "Registrar restrições legais, administrativas ou físicas.",
      exemplo: "Acesso público, exceto documentos com dados pessoais.",
    },
  },
  ISAD_G: {
    codigo_referencia: {
      oficial: "Reference code",
      finalidade: "Identificar unicamente a unidade de descrição.",
      regra: "Registrar código nacional, local e específico da unidade.",
      exemplo: "BR SPAPESP EDU 001",
    },
    titulo: {
      oficial: "Title",
      finalidade: "Nomear a unidade de descrição.",
      regra: "Informar título formal ou atribuído, de forma concisa.",
      exemplo: "Fundo Secretaria da Educação",
    },
    nivel: {
      oficial: "Level of description",
      finalidade: "Indicar a posição da unidade na descrição multinível.",
      regra: "Usar nível coerente com a estrutura hierárquica.",
      exemplo: "Series",
    },
    produtor: {
      oficial: "Name of creator(s)",
      finalidade: "Registrar pessoa ou entidade produtora.",
      regra: "Usar forma normalizada do nome quando possível.",
      exemplo: "Department of Education",
    },
    condicoes_acesso: {
      oficial: "Conditions governing access",
      finalidade: "Registrar condições que afetam a disponibilidade da unidade.",
      regra: "Indicar restrições e bases legais ou administrativas.",
      exemplo: "Open access with personal data restrictions.",
    },
  },
};

export function getHelp(norma: NormaDescricao, field: string) {
  return helpTexts[norma][field] ?? {
    oficial: field.replaceAll("_", " "),
    finalidade: "Elemento descritivo previsto no perfil normativo.",
    regra: "Preencher de forma objetiva, evitando repetição de informação herdada.",
    exemplo: "Informação pertinente à unidade de descrição.",
  };
}
