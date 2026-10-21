"use client";
import { Plus } from "lucide-react";
import type { JobImportacao } from "@/lib/importacoes-assincronas";
import type { Mapeamento, NovoCampo } from "@/lib/importacoes";
import type { TipoCampo } from "@/types/domain";

type Analise = NonNullable<JobImportacao["analise"]>;
const tipos: TipoCampo[] = ["TEXTO_CURTO", "TEXTO_LONGO", "NUMERO", "DATA", "BOOLEANO", "LISTA_SIMPLES", "LISTA_MULTIPLA", "URL"];
export function sugerirMapeamentos(analise: Analise): Mapeamento[] {
  return analise.colunas.map(coluna => ({
    origem: coluna.origem,
    destino: analise.campos.find(campo => campo.chave === coluna.chave_sugerida ||
      campo.nome.localeCompare(coluna.origem, "pt-BR", { sensitivity: "base" }) === 0)?.chave || ""
  }));
}
export function displayImportacao(value: unknown): string {
  if (value == null || value === "") return "-";
  if (typeof value === "boolean") return value ? "Sim" : "Nao";
  return typeof value === "object" ? JSON.stringify(value) : String(value);
}
export function ImportacaoMapeamento({ analise, value, onChange, canCreateFields, disabled }: {
  analise: Analise; value: Mapeamento[]; onChange: (value: Mapeamento[]) => void; canCreateFields: boolean; disabled: boolean;
}) {
  function novo(origem: string): NovoCampo {
    const coluna = analise.colunas.find(item => item.origem === origem)!;
    return { nome: origem, chave: coluna.chave_sugerida, tipo: coluna.tipo_sugerido, obrigatorio: false };
  }
  function change(index: number, mapping: Mapeamento) {
    onChange(value.map((item, position) => position === index ? mapping : item));
  }
  return <>
    <div className="row"><h2>Associacao de campos</h2>
      {canCreateFields && <button className="button secondary" type="button" disabled={disabled}
        onClick={() => onChange(value.map(item => item.destino || item.novo ? item : { origem: item.origem, novo: novo(item.origem) }))}>
        <Plus size={16}/>Criar campos nao associados</button>}
    </div>
    <fieldset className="registro-fields" disabled={disabled}>
      <div className="table-wrap"><table className="table importacao-mapping" aria-label="Associacao de campos">
        <thead><tr><th>Coluna do arquivo</th><th>Exemplo</th><th>Associar a</th><th>Novo campo</th></tr></thead>
        <tbody>{value.map((mapping, index) => <tr key={mapping.origem}>
          <td className="break-text">{mapping.origem}</td>
          <td className="break-text">{displayImportacao(analise.colunas.find(item => item.origem === mapping.origem)?.amostras[0]).slice(0, 160)}</td>
          <td><select className="select" aria-label={"Associar " + mapping.origem} value={mapping.novo ? "__novo" : mapping.destino || ""}
            onChange={event => change(index, event.target.value === "__novo"
              ? { origem: mapping.origem, novo: novo(mapping.origem) } : { origem: mapping.origem, destino: event.target.value })}>
            <option value="">Ignorar</option>{analise.campos.map(campo => <option key={campo.chave} value={campo.chave}>{campo.nome}</option>)}
            {canCreateFields && <option value="__novo">Criar novo campo</option>}
          </select></td>
          <td>{mapping.novo ? <div className="stack">
            <label className="field"><span>Nome *</span><input className="input" required maxLength={255}
              aria-label={"Nome do campo " + mapping.origem} disabled={!canCreateFields} value={mapping.novo.nome}
              onChange={event => change(index, { ...mapping, novo: { ...mapping.novo!, nome: event.target.value } })}/></label>
            <label className="field"><span>Chave *</span><input className="input" required maxLength={100} pattern="[a-zA-Z][a-zA-Z0-9_]*"
              aria-label={"Chave do campo " + mapping.origem} disabled={!canCreateFields} value={mapping.novo.chave}
              onChange={event => change(index, { ...mapping, novo: { ...mapping.novo!, chave: event.target.value } })}/></label>
            <label className="field"><span>Tipo *</span><select className="select" aria-label={"Tipo do campo " + mapping.origem}
              disabled={!canCreateFields} value={mapping.novo.tipo}
              onChange={event => change(index, { ...mapping, novo: { ...mapping.novo!, tipo: event.target.value as TipoCampo } })}>
              {tipos.map(tipo => <option key={tipo} value={tipo}>{tipo.replaceAll("_", " ")}</option>)}
            </select></label>
            <label className="checkbox-field"><input type="checkbox" disabled={!canCreateFields} checked={mapping.novo.obrigatorio}
              onChange={event => change(index, { ...mapping, novo: { ...mapping.novo!, obrigatorio: event.target.checked } })}/>Obrigatorio</label>
          </div> : "-"}</td>
        </tr>)}</tbody>
      </table></div>
    </fieldset>
  </>;
}
