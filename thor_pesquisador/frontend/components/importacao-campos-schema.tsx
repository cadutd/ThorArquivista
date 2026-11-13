"use client";
import { Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { getSchema, request } from "@/lib/api";
import type { InstrumentoCampo, TipoCampo } from "@/types/domain";
import { ModalFrame } from "./modal-frame";

type FormularioCampo = Omit<InstrumentoCampo, "id" | "instrumento_id" | "opcoes" | "validacoes"> & {
  opcoesJson: string;
  validacoesJson: string;
};
type SchemaCampos = { schema_version: number; campos: InstrumentoCampo[] };

const tipos: TipoCampo[] = ["TEXTO_CURTO", "TEXTO_LONGO", "NUMERO", "DATA", "BOOLEANO", "LISTA_SIMPLES", "LISTA_MULTIPLA", "URL"];

export function ImportacaoCamposSchema({ instrumentoId, campos, canEdit, canDelete, disabled, onBusyChange, onSchemaChange }: {
  instrumentoId: string;
  campos: InstrumentoCampo[];
  canEdit: boolean;
  canDelete: boolean;
  disabled: boolean;
  onBusyChange: (busy: boolean) => void;
  onSchemaChange: (schema: SchemaCampos, anterior: InstrumentoCampo, atualizado?: InstrumentoCampo) => void;
}) {
  const [selected, setSelected] = useState<InstrumentoCampo>();
  const [form, setForm] = useState<FormularioCampo>();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function working(value: boolean) {
    setBusy(value);
    onBusyChange(value);
  }
  function editar(campo: InstrumentoCampo) {
    setSelected(campo);
    setForm({
      nome: campo.nome,
      chave: campo.chave,
      tipo: campo.tipo,
      ordem: campo.ordem,
      obrigatorio: campo.obrigatorio,
      multiplo: campo.multiplo,
      opcoesJson: campo.opcoes == null ? "" : JSON.stringify(campo.opcoes, null, 2),
      validacoesJson: campo.validacoes == null ? "" : JSON.stringify(campo.validacoes, null, 2),
      aparece_cadastro: campo.aparece_cadastro,
      aparece_listagem: campo.aparece_listagem,
      aparece_busca: campo.aparece_busca,
      exibir_publico: !!campo.exibir_publico,
      filtro_avancado: campo.filtro_avancado,
      facetavel: campo.facetavel,
      ordenavel: campo.ordenavel,
    });
    setError("");
  }
  function fechar() {
    if (busy) return;
    setSelected(undefined);
    setForm(undefined);
    setError("");
  }
  async function recarregarSchema(anterior: InstrumentoCampo, atualizado?: InstrumentoCampo) {
    try {
      const schema = await getSchema(instrumentoId);
      onSchemaChange(schema, anterior, atualizado);
    } catch (err) {
      throw new Error("Campo salvo, mas nao foi possivel atualizar o schema da importacao. Recarregue a pagina antes de validar.");
    }
  }
  async function salvar(event: React.FormEvent) {
    event.preventDefault();
    if (!selected || !form || !canEdit || disabled || busy) return;
    setError("");
    working(true);
    let saved = false;
    try {
      const updated = await request<InstrumentoCampo>("/instrumentos/" + instrumentoId + "/campos/" + selected.id, {
        method: "PUT",
        body: JSON.stringify({
          nome: form.nome.trim(),
          chave: form.chave.trim(),
          tipo: form.tipo,
          ordem: form.ordem,
          obrigatorio: form.obrigatorio,
          multiplo: form.multiplo,
          opcoes: parseJson(form.opcoesJson, "Opcoes"),
          validacoes: parseJson(form.validacoesJson, "Validacoes"),
          aparece_cadastro: form.aparece_cadastro,
          aparece_listagem: form.aparece_listagem,
          aparece_busca: form.aparece_busca,
          exibir_publico: form.exibir_publico,
          filtro_avancado: form.filtro_avancado,
          facetavel: form.facetavel,
          ordenavel: form.ordenavel,
        }),
      });
      saved = true;
      await recarregarSchema(selected, updated);
      setSelected(undefined);
      setForm(undefined);
    } catch (err) {
      setError(saved
        ? err instanceof Error ? err.message : "Campo salvo, mas falhou ao atualizar o schema da importacao."
        : err instanceof Error ? err.message : "Falha ao salvar campo.");
    } finally {
      working(false);
    }
  }
  async function excluir(campo: InstrumentoCampo) {
    if (!canDelete || disabled || busy) return;
    if (!window.confirm("Excluir o campo \"" + campo.nome + "\" do instrumento? Valores ja salvos nos registros serao preservados, mas o campo deixara de aparecer no schema.")) return;
    setError("");
    working(true);
    let saved = false;
    try {
      await request("/instrumentos/" + instrumentoId + "/campos/" + campo.id, { method: "DELETE" });
      saved = true;
      await recarregarSchema(campo);
    } catch (err) {
      setError(saved
        ? err instanceof Error ? err.message : "Campo excluido, mas falhou ao atualizar o schema da importacao."
        : err instanceof Error ? err.message : "Falha ao excluir campo.");
    } finally {
      working(false);
    }
  }

  if (!canEdit && !canDelete) return null;
  return <section className="panel stack">
    <h2>Campos do instrumento</h2>
    <p className="muted">Alteracoes sao persistentes e atualizam o schema do instrumento. Valores ja salvos nao sao convertidos.</p>
    <div className="table-wrap"><table className="table" aria-label="Campos existentes do instrumento">
      <thead><tr><th>Nome</th><th>Chave</th><th>Tipo</th><th>Obrigatorio</th><th>Acoes</th></tr></thead>
      <tbody>{campos.length ? campos.map(campo => <tr key={campo.id}>
        <td className="break-text">{campo.nome}</td><td className="break-text">{campo.chave}</td><td>{campo.tipo}</td>
        <td>{campo.obrigatorio ? "Sim" : "Nao"}</td><td><div className="actions">
          {canEdit && <button className="icon-button" type="button" title={"Editar campo " + campo.nome}
            aria-label={"Editar campo " + campo.nome} disabled={disabled || busy} onClick={() => editar(campo)}><Pencil size={16}/></button>}
          {canDelete && <button className="icon-button danger" type="button" title={"Excluir campo " + campo.nome}
            aria-label={"Excluir campo " + campo.nome} disabled={disabled || busy} onClick={() => excluir(campo)}><Trash2 size={16}/></button>}
        </div></td>
      </tr>) : <tr><td colSpan={5}>Nenhum campo existente.</td></tr>}</tbody>
    </table></div>
    {error && <p className="error" role="alert">{error}</p>}
    {selected && form && <ModalFrame title={"Editar campo " + selected.nome} onClose={fechar}>
      <form className="stack" onSubmit={salvar}>
        <div className="row"><h2>Editar campo</h2><button className="button secondary" type="button" disabled={busy} onClick={fechar}>Fechar</button></div>
        <p className="muted">Salvar altera o schema do instrumento, pode invalidar uma publicacao vigente e nao converte dados ja gravados.</p>
        <fieldset className="stack" disabled={busy || disabled}>
          <div className="grid">
            <label className="field"><span>Nome *</span><input className="input" required maxLength={255} value={form.nome}
              onChange={event => setForm({ ...form, nome: event.target.value })}/></label>
            <label className="field"><span>Chave *</span><input className="input" required maxLength={100} pattern="[a-zA-Z][a-zA-Z0-9_]*" value={form.chave}
              onChange={event => setForm({ ...form, chave: event.target.value })}/></label>
            <label className="field"><span>Tipo *</span><select className="select" value={form.tipo}
              onChange={event => setForm({ ...form, tipo: event.target.value as TipoCampo })}>
              {tipos.map(tipo => <option key={tipo} value={tipo}>{tipo.replaceAll("_", " ")}</option>)}
            </select></label>
            <label className="field"><span>Ordem</span><input className="input" type="number" min={0} step={1} value={form.ordem}
              onChange={event => setForm({ ...form, ordem: Number(event.target.value) })}/></label>
          </div>
          <div className="actions">
            <CheckField label="Obrigatorio" value={form.obrigatorio} onChange={value => setForm({ ...form, obrigatorio: value })}/>
            <CheckField label="Multiplo" value={form.multiplo} onChange={value => setForm({ ...form, multiplo: value })}/>
            <CheckField label="Cadastro" value={form.aparece_cadastro} onChange={value => setForm({ ...form, aparece_cadastro: value })}/>
            <CheckField label="Listagem" value={form.aparece_listagem} onChange={value => setForm({ ...form, aparece_listagem: value })}/>
            <CheckField label="Busca" value={form.aparece_busca} onChange={value => setForm({ ...form, aparece_busca: value })}/>
            <CheckField label="Exibir publico" value={!!form.exibir_publico} onChange={value => setForm({ ...form, exibir_publico: value })}/>
            <CheckField label="Filtro avancado" value={form.filtro_avancado} onChange={value => setForm({ ...form, filtro_avancado: value })}/>
            <CheckField label="Facetavel" value={form.facetavel} onChange={value => setForm({ ...form, facetavel: value })}/>
            <CheckField label="Ordenavel" value={form.ordenavel} onChange={value => setForm({ ...form, ordenavel: value })}/>
          </div>
          <label className="field"><span>Opcoes (JSON)</span><textarea className="textarea" rows={4} value={form.opcoesJson}
            onChange={event => setForm({ ...form, opcoesJson: event.target.value })}/></label>
          <label className="field"><span>Validacoes (JSON)</span><textarea className="textarea" rows={4} value={form.validacoesJson}
            onChange={event => setForm({ ...form, validacoesJson: event.target.value })}/></label>
        </fieldset>
        {error && <p className="error" role="alert">{error}</p>}
        <div className="actions"><button className="button" type="submit" disabled={busy || disabled}>
          {busy ? "Salvando..." : "Salvar alteracoes"}
        </button></div>
      </form>
    </ModalFrame>}
  </section>;
}

function parseJson(value: string, label: string): unknown {
  if (!value.trim()) return null;
  const result: unknown = JSON.parse(value);
  if (result === null || typeof result !== "object")
    throw new Error(label + " deve ser um objeto ou uma lista JSON.");
  return result;
}

function CheckField({ label, value, onChange }: { label: string; value: boolean; onChange: (value: boolean) => void }) {
  return <label className="checkbox-field"><input type="checkbox" checked={value}
    onChange={event => onChange(event.target.checked)}/>{label}</label>;
}
