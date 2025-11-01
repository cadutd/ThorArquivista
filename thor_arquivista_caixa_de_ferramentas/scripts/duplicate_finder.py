#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/duplicate_finder.py — Localizador de duplicidades (SHA256) com relatórios

Padrão: segue o estilo dos demais scripts desta pasta (argparse simples, logs [OK]/[INFO]/[WARN],
sem dependências obrigatórias além da biblioteca padrão; suporte opcional a Excel via pandas/xlsxwriter).

Funcionalidades principais:
  1) Inventário de arquivos com SHA256 e metadados de tempo
  2) Detecção de duplicatas por (hash,tamanho) com listagem de caminhos
  3) Geração de modelo de decisões (manter/eliminar/justificativa)
  4) Geração de script de tratamento (Linux/Windows) para quarentena ou remoção direta, com LOG
  5) Dashboards de espaço recuperável (potencial e planejado) em CSV e opcionalmente Excel
"""
import argparse
import csv
import hashlib
import os
import sys
from datetime import datetime
from typing import Dict, Iterator, List, Optional, Tuple

# Dependências opcionais para exportar Excel
try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None

# ------------------------- Utilitários -------------------------

CHUNK_SIZE = 1024 * 1024  # 1 MiB

def _log_info(msg: str) -> None:
    print(f"[INFO] {msg}", file=sys.stderr)

def _log_ok(msg: str) -> None:
    print(f"[OK] {msg}")

def _log_warn(msg: str) -> None:
    print(f"[WARN] {msg}", file=sys.stderr)

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def iter_files(root: str) -> Iterator[str]:
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            yield os.path.join(dirpath, name)

def relpath(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root).replace('\\', '/')
    except Exception:
        return path

def top_level_folder(rel_path: str) -> str:
    p = rel_path.strip().lstrip('/')
    return p.split('/', 1)[0] if p else ''

def human_bytes(n: int) -> str:
    units = ['B','KB','MB','GB','TB','PB']
    size = float(n)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{size:.2f} {u}"
        size /= 1024.0

def load_inventory_map(inventario_csv: str) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Retorna:
       - path_to_size: tamanho por caminho_relativo
       - hash_to_size: tamanho por hash
    """
    path_to_size: Dict[str, int] = {}
    hash_to_size: Dict[str, int] = {}
    with open(inventario_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            rel = row['caminho_relativo'].strip()
            size = int(row['tamanho'])
            h = row['sha256'].strip()
            path_to_size[rel] = size
            hash_to_size[h] = size
    return path_to_size, hash_to_size

# ------------------------- Núcleo -------------------------

def inventariar(raiz: str, inventario_csv: str, show_progress: bool = True) -> int:
    raiz = os.path.abspath(raiz)
    total = 0
    with open(inventario_csv, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out)
        w.writerow(['sha256','tamanho','caminho_relativo','ctime','mtime'])
        for path in iter_files(raiz):
            try:
                st = os.stat(path)
                size = st.st_size
                digest = sha256_file(path)
                rpath = relpath(path, raiz)
                ctime = datetime.fromtimestamp(st.st_ctime).isoformat()
                mtime = datetime.fromtimestamp(st.st_mtime).isoformat()
                w.writerow([digest, size, rpath, ctime, mtime])
                total += 1
                if show_progress and total % 200 == 0:
                    _log_info(f"Processados {total} arquivos...")
            except (PermissionError, FileNotFoundError) as e:
                _log_warn(f"Ignorado (sem acesso/movido): {path} -> {e}")
    _log_ok(f"Inventário gerado: {inventario_csv} (arquivos: {total})")
    return total

def detectar_duplicatas(inventario_csv: str, duplicatas_csv: str) -> int:
    grupos: Dict[str, List[str]] = {}
    tamanhos: Dict[str, int] = {}

    with open(inventario_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            key = f"{row['sha256']}|{row['tamanho']}"
            grupos.setdefault(key, []).append(row['caminho_relativo'])
            tamanhos[key] = int(row['tamanho'])

    total_dups = 0
    with open(duplicatas_csv, 'w', newline='', encoding='utf-8') as out:
        w = csv.writer(out)
        w.writerow(['hash','tamanho','ocorrencias','caminhos'])
        for key, paths in grupos.items():
            if len(paths) > 1:
                digest, tamanho = key.split('|', 1)
                w.writerow([digest, tamanho, len(paths), ' | '.join(sorted(paths))])
                total_dups += 1

    _log_ok(f"Duplicatas detectadas: {total_dups} grupos -> {duplicatas_csv}")
    return total_dups

def gerar_modelo_decisoes(duplicatas_csv: str, decisoes_csv: str) -> int:
    rows = 0
    with open(duplicatas_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        with open(decisoes_csv, 'w', newline='', encoding='utf-8') as out:
            w = csv.DictWriter(out, fieldnames=['hash','caminho_mantido','caminhos_eliminados','justificativa','responsavel','data_decisao'])
            w.writeheader()
            for row in r:
                caminhos = [c.strip() for c in row['caminhos'].split('|') if c.strip()]
                caminhos.sort()
                manter = caminhos[0] if caminhos else ''
                eliminar = [c for c in caminhos if c != manter]
                w.writerow({
                    'hash': row['hash'],
                    'caminho_mantido': manter,
                    'caminhos_eliminados': ' | '.join(eliminar),
                    'justificativa': 'Manter na estrutura oficial do fundo/serie. (Editar conforme análise de proveniência)',
                    'responsavel': '',
                    'data_decisao': ''
                })
                rows += 1
    _log_ok(f"Modelo de decisões gerado: {decisoes_csv} ({rows} linhas)")
    return rows

def gerar_script_remocao(decisoes_csv: str, script_path: str, sistema: str = "linux", acao: str = "quarentena",
                         prefixo_quarentena: str = "quarentena", log_nome: Optional[str] = None) -> None:
    """
    Gera um script para processamento das cópias marcadas em 'decisoes.csv'.
    - sistema: "linux" (bash .sh) ou "windows" (batch .cmd)
    - acao: "quarentena" (mover) ou "remover" (apagar DEFINITIVAMENTE)
    - prefixo_quarentena: prefixo do diretório de quarentena (ex.: 'quarentena')
    - log_nome: nome do arquivo de log gerado pelo script (se None, usa padrão tratamento_YYYYMMDD_HHMMSS.log)
    Observação: sempre pede confirmação explícita do operador antes de executar.
    """
    sistema = (sistema or "linux").strip().lower()
    acao = (acao or "quarentena").strip().lower()
    if sistema not in {"linux","windows"}:
        raise ValueError("sistema deve ser 'linux' ou 'windows'")
    if acao not in {"quarentena","remover"}:
        raise ValueError("acao deve ser 'quarentena' ou 'remover'")

    # Coleta de caminhos-alvo a partir de decisoes.csv
    alvos: List[str] = []
    with open(decisoes_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            for path in [c.strip() for c in row.get('caminhos_eliminados','').split('|') if c.strip()]:
                alvos.append(path)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_nome or f"tratamento_{ts}.log"

    if sistema == "linux":
        lines: List[str] = [
            "#!/usr/bin/env bash",
            f'LOG_FILE="{log_file}"',
            'echo "[INFO] Script de tratamento de duplicidades" | tee -a "$LOG_FILE"',
        ]
        if acao == "quarentena":
            quarantine_dir = f"{prefixo_quarentena}_{ts}"
            lines += [
                f'QUARENTENA="{quarantine_dir}"',
                'mkdir -p "$QUARENTENA"',
                'echo "[INFO] Quarentena em: $QUARENTENA" | tee -a "$LOG_FILE"',
                'read -p "CONFIRMAR operacao (digite YES para continuar): " OK',
                'if [ "$OK" != "YES" ]; then echo "Abortado." | tee -a "$LOG_FILE"; exit 1; fi',
                ""
            ]
            for path in alvos:
                # verifica existência; move preservando subpastas; loga tudo
                lines.append(f'if [ ! -e "{path}" ]; then echo "[WARN] Nao encontrado: {path}" | tee -a "$LOG_FILE"; '
                             f'else mkdir -p "$QUARENTENA/$(dirname "{path}")" && mv -v -- "{path}" "$QUARENTENA/{path}" 2>&1 | tee -a "$LOG_FILE"; fi')
        else:
            lines += [
                'read -p "REMOVER DEFINITIVAMENTE os arquivos? (digite DELETE): " OK',
                'if [ "$OK" != "DELETE" ]; then echo "Abortado." | tee -a "$LOG_FILE"; exit 1; fi',
                ""
            ]
            for path in alvos:
                lines.append(f'if [ ! -e "{path}" ]; then echo "[WARN] Nao encontrado: {path}" | tee -a "$LOG_FILE"; '
                             f'else rm -v -- "{path}" 2>&1 | tee -a "$LOG_FILE"; fi')

        content = "\n".join(lines) + "\n"
        with open(script_path, 'w', encoding='utf-8') as out:
            out.write(content)

    else:  # WINDOWS
        # Usamos PowerShell para criar diretórios e mover/remover com suporte a acentuação/caminhos longos.
        lines = [
            "@echo off",
            "setlocal enabledelayedexpansion",
            f'set "LOG_FILE=%cd%\\{log_file}"',
            "echo [INFO] Script de tratamento de duplicidades",
            "echo Iniciando... >> %LOG_FILE%",
        ]
        if acao == "quarentena":
            quarantine_dir = f"{prefixo_quarentena}_{ts}"
            lines += [
                f'set "QUARENTENA={quarantine_dir}"',
                'powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path \\"%QUARENTENA%\\" | Out-Null"',
                'echo [INFO] Quarentena em: %QUARENTENA%',
                'set /p OK=CONFIRMAR operacao (digite YES para continuar): ',
                'if /I not "%OK%"=="YES" ( echo Abortado. & echo Abortado.>> %LOG_FILE% & exit /b 1 )',
                ""
            ]
            for path in alvos:
                quoted = path.replace('"', '\\"')
                lines.append(
                    'powershell -NoProfile -Command ' +
                    f'"$p=\\"{quoted}\\"; ' +
                    'if (-Not (Test-Path -LiteralPath $p)) { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[WARN] Nao encontrado: \\" + $p); exit 0 } ; ' +
                    '$d=[System.IO.Path]::GetDirectoryName($p); if ($d -and $d -ne \\"\\") { New-Item -ItemType Directory -Force -Path (\\"%QUARENTENA%\\\\\\" + $d) | Out-Null }; ' +
                    'Move-Item -Force -LiteralPath $p -Destination (\\"%QUARENTENA%\\\\\\" + $p) -ErrorAction SilentlyContinue; ' +
                    'if ($?) { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[OK] Movido: \\" + $p) } else { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[WARN] Falha ao mover: \\" + $p) }"'
                )
        else:
            lines += [
                'set /p OK=REMOVER DEFINITIVAMENTE os arquivos? (digite DELETE): ',
                'if /I not "%OK%"=="DELETE" ( echo Abortado. & echo Abortado.>> %LOG_FILE% & exit /b 1 )',
                ""
            ]
            for path in alvos:
                quoted = path.replace('"', '\\"')
                lines.append(
                    'powershell -NoProfile -Command ' +
                    f'"$p=\\"{quoted}\\"; ' +
                    'if (-Not (Test-Path -LiteralPath $p)) { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[WARN] Nao encontrado: \\" + $p); exit 0 } ; ' +
                    'Remove-Item -Force -LiteralPath $p -ErrorAction SilentlyContinue; ' +
                    'if ($?) { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[OK] Removido: \\" + $p) } else { Add-Content -Path \\"%LOG_FILE%\\" -Value (\\"[WARN] Falha ao remover: \\" + $p) }"'
                )

        content = "\n".join(lines) + "\n"
        with open(script_path, 'w', encoding='utf-8') as out:
            out.write(content)

    try:
        os.chmod(script_path, 0o755)
    except Exception:
        pass

    _log_ok(f"Script de {'quarentena' if acao=='quarentena' else 'remoção'} ({sistema}) gerado: {script_path}")

# ------------------------- Dashboards -------------------------

def dashboard_from_duplicatas(inventario_csv: str, duplicatas_csv: str, out_csv: str, out_xlsx: Optional[str] = None) -> Tuple[int, int]:
    """Potencial de recuperação: (ocorrencias - 1) * tamanho, por grupo de duplicatas."""
    grupos = []
    total_pot = 0
    redund = 0

    with open(duplicatas_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            tamanho = int(row['tamanho']); ocorr = int(row['ocorrencias'])
            potencial = max(0, ocorr - 1) * tamanho
            total_pot += potencial
            redund += max(0, ocorr - 1)
            grupos.append({
                'hash': row['hash'],
                'tamanho': tamanho,
                'ocorrencias': ocorr,
                'potencial_recuperacao_bytes': potencial,
                'potencial_recuperacao_humano': human_bytes(potencial),
                'caminhos': row['caminhos']
            })

    with open(out_csv, 'w', newline='', encoding='utf-8') as out:
        w = csv.DictWriter(out, fieldnames=['hash','tamanho','ocorrencias','potencial_recuperacao_bytes','potencial_recuperacao_humano','caminhos'])
        w.writeheader()
        for g in grupos:
            w.writerow(g)

    if out_xlsx and pd is not None:
        import pandas as _pd
        resumo = _pd.DataFrame([{
            'grupos_duplicados': len(grupos),
            'arquivos_redundantes': redund,
            'potencial_recuperacao_bytes': total_pot,
            'potencial_recuperacao_humano': human_bytes(total_pot)
        }])
        df_grupos = _pd.DataFrame(grupos)

        # Alocar potencial à pasta topo do 1º caminho de cada grupo
        topo_rows = []
        for g in grupos:
            caminhos = [c.strip() for c in g['caminhos'].split('|') if c.strip()]
            topo = top_level_folder(caminhos[0]) if caminhos else ''
            topo_rows.append({'pasta_topo': topo, 'potencial_recuperacao_bytes': g['potencial_recuperacao_bytes']})
        df_topo = _pd.DataFrame(topo_rows).groupby('pasta_topo', dropna=False)['potencial_recuperacao_bytes'].sum().reset_index()
        df_topo['potencial_recuperacao_humano'] = df_topo['potencial_recuperacao_bytes'].apply(human_bytes)

        with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
            resumo.to_excel(writer, index=False, sheet_name="Resumo")
            df_grupos.to_excel(writer, index=False, sheet_name="Grupos")
            df_topo.to_excel(writer, index=False, sheet_name="PorPastaTopo")

    _log_ok(f"Dashboard (duplicatas) CSV: {out_csv} | Potencial: {human_bytes(total_pot)}")
    return redund, total_pot

def dashboard_from_decisoes(inventario_csv: str, decisoes_csv: str, out_csv: str, out_xlsx: Optional[str] = None) -> Tuple[int, int, int]:
    """Recuperação planejada: soma dos tamanhos dos 'caminhos_eliminados' encontrados no inventário."""
    path_to_size, _ = load_inventory_map(inventario_csv)

    linhas = []
    missing = []
    total = 0

    with open(decisoes_csv, 'r', encoding='utf-8') as f:
        r = csv.DictReader(f)
        for row in r:
            h = row.get('hash','').strip()
            eliminar = [c.strip() for c in row.get('caminhos_eliminados','').split('|') if c.strip()]
            for p in eliminar:
                size = path_to_size.get(p)
                if size is None:
                    missing.append({'hash': h, 'caminho': p})
                    continue
                linhas.append({'hash': h, 'caminho_eliminado': p, 'tamanho': size})
                total += size

    with open(out_csv, 'w', newline='', encoding='utf-8') as out:
        w = csv.DictWriter(out, fieldnames=['hash','caminho_eliminado','tamanho'])
        w.writeheader()
        for l in linhas:
            w.writerow(l)

    if out_xlsx and pd is not None:
        import pandas as _pd
        resumo = _pd.DataFrame([{
            'itens_planejados_eliminacao': len(linhas),
            'recuperacao_planejada_bytes': total,
            'recuperacao_planejada_humano': human_bytes(total),
            'nao_encontrados_inventario': len(missing)
        }])
        df_detalhe = _pd.DataFrame(linhas)
        acc = {}
        for l in linhas:
            topo = top_level_folder(l['caminho_eliminado'])
            acc[topo] = acc.get(topo, 0) + l['tamanho']
        df_topo = _pd.DataFrame([{'pasta_topo': k, 'bytes': v} for k, v in acc.items()]).sort_values('bytes', ascending=False)
        if not df_topo.empty:
            df_topo['humano'] = df_topo['bytes'].apply(human_bytes)
        df_missing = _pd.DataFrame(missing)

        with pd.ExcelWriter(out_xlsx, engine="xlsxwriter") as writer:
            resumo.to_excel(writer, index=False, sheet_name="Resumo")
            df_detalhe.to_excel(writer, index=False, sheet_name="Detalhe")
            df_topo.to_excel(writer, index=False, sheet_name="PorPastaTopo")
            if not df_missing.empty:
                df_missing.to_excel(writer, index=False, sheet_name="NaoEncontrados")

    _log_ok(f"Dashboard (decisões) CSV: {out_csv} | Planejado: {human_bytes(total)} | Não encontrados: {len(missing)}")
    return len(linhas), total, len(missing)

# ------------------------- CLI -------------------------

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Detecta duplicidades por SHA256, gera relatórios/decisões e dashboards.")
    p.add_argument('--raiz', help='Pasta raiz a inventariar')
    p.add_argument('--inventario', help='Arquivo CSV de inventário (entrada/saída)')
    p.add_argument('--duplicatas', help='Arquivo CSV de duplicatas (entrada/saída)')
    p.add_argument('--from-duplicatas', help='Usar duplicatas.csv para gerar modelo de decisões')
    p.add_argument('--decisoes', help='Arquivo CSV de decisões (entrada/saída)')

    # Script de tratamento
    p.add_argument('--gerar-script-remocao', help='Gerar script de tratamento (quarentena/remocao) para Linux (.sh) ou Windows (.cmd)')
    p.add_argument('--sistema', choices=['linux','windows'], default='linux', help='Sistema-alvo do script de tratamento (default: linux)')
    p.add_argument('--acao', choices=['quarentena','remover'], default='quarentena', help='Ação do script: mover para quarentena ou remover definitivo (default: quarentena)')
    p.add_argument('--prefixo-quarentena', default='quarentena', help='Prefixo do diretório de quarentena (default: quarentena)')
    p.add_argument('--script-log-nome', help='Nome do arquivo de log gerado pelo script (ex.: tratamento_20250101_120000.log). Se omitido, o script define um padrão.')

    p.add_argument('--mostrar-progresso', action='store_true', help='Exibe progresso no inventário (a cada 200 arquivos)')

    # Dashboards
    p.add_argument('--dashboard-duplicatas-csv', help='CSV do potencial de recuperação (base duplicatas)')
    p.add_argument('--dashboard-duplicatas-xlsx', help='XLSX do potencial de recuperação (requer pandas+xlsxwriter)')
    p.add_argument('--dashboard-decisoes-csv', help='CSV da recuperação planejada (base decisões)')
    p.add_argument('--dashboard-decisoes-xlsx', help='XLSX da recuperação planejada (requer pandas+xlsxwriter)')
    return p

def main() -> None:
    args = _build_parser().parse_args()

    # Rotas exclusivas (um comando por execução, como nos outros scripts)
    if args.raiz and args.inventario and not any([
        args.duplicatas, args.from_duplicatas, args.decisoes, args.gerar_script_remocao,
        args.dashboard_duplicatas_csv, args.dashboard_duplicatas_xlsx, args.dashboard_decisoes_csv, args.dashboard_decisoes_xlsx
    ]):
        inventariar(args.raiz, args.inventario, show_progress=args.mostrar_progresso); return

    if args.inventario and args.duplicatas and not any([
        args.raiz, args.from_duplicatas, args.decisoes, args.gerar_script_remocao,
        args.dashboard_duplicatas_csv, args.dashboard_duplicatas_xlsx, args.dashboard_decisoes_csv, args.dashboard_decisoes_xlsx
    ]):
        detectar_duplicatas(args.inventario, args.duplicatas); return

    if args.from_duplicatas and args.decisoes and not any([
        args.raiz, args.inventario, args.duplicatas, args.gerar_script_remocao,
        args.dashboard_duplicatas_csv, args.dashboard_duplicatas_xlsx, args.dashboard_decisoes_csv, args.dashboard_decisoes_xlsx
    ]):
        gerar_modelo_decisoes(args.from_duplicatas, args.decisoes); return

    if args.decisoes and args.gerar_script_remocao and not any([
        args.raiz, args.inventario, args.duplicatas, args.from_duplicatas,
        args.dashboard_duplicatas_csv, args.dashboard_duplicatas_xlsx, args.dashboard_decisoes_csv, args.dashboard_decisoes_xlsx
    ]):
        gerar_script_remocao(args.decisoes, args.gerar_script_remocao, sistema=args.sistema, acao=args.acao,
                             prefixo_quarentena=args.prefixo_quarentena, log_nome=args.script_log_nome); return

    # Dashboards
    if args.inventario and args.duplicatas and (args.dashboard_duplicatas_csv or args.dashboard_duplicatas_xlsx):
        out_csv = args.dashboard_duplicatas_csv or "dashboard_duplicatas.csv"
        dashboard_from_duplicatas(args.inventario, args.duplicatas, out_csv, args.dashboard_duplicatas_xlsx); return

    if args.inventario and args.decisoes and (args.dashboard_decisoes_csv or args.dashboard_decisoes_xlsx):
        out_csv = args.dashboard_decisoes_csv or "dashboard_decisoes.csv"
        dashboard_from_decisoes(args.inventario, args.decisoes, out_csv, args.dashboard_decisoes_xlsx); return

    _build_parser().print_help()

if __name__ == '__main__':
    main()
