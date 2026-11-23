#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from backup_common import (
    append_premis,
    backup_report_summary,
    copy_file,
    destination,
    digest_file,
    ensure_repository,
    load_plan,
    normalize_sources,
    options,
    plan_name,
    read_json,
    read_source_manifests,
    run_id,
    source_manifest_path,
    validate_source_paths,
    write_json,
    write_source_manifests,
    write_backup_report,
)
from backup_manifest_build import build_manifest
from backup_manifest_diff import diff_manifests


def progress_marks(total: int) -> list[tuple[int, int]]:
    marks_by_count = {}
    for percent in range(5, 101, 5):
        mark = max(1, (total * percent + 99) // 100)
        marks_by_count[mark] = percent
    return sorted(marks_by_count.items())


def emit_progress(done: int, total: int, marks: list[tuple[int, int]], next_mark: int, label: str) -> int:
    while next_mark < len(marks) and done >= marks[next_mark][0]:
        percent = marks[next_mark][1]
        print(f"[INFO] {label} {percent}%: processados {done}/{total}; faltam {total - done}")
        next_mark += 1
    return next_mark


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Executa backup preservacional incremental com manifesto por origem.")
    p.add_argument("--config", required=True, help="Plano JSON do backup.")
    p.add_argument("--resume", action="store_true", help="Retoma a execução a partir do checkpoint.")
    p.add_argument("--premis-log", help="Arquivo JSONL PREMIS. Padrão: thor-backup/logs/premis_events.jsonl.")
    p.add_argument("--agent", default="Thor Arquivista backup_plan.py", help="Agente PREMIS.")
    p.add_argument("--progress", action="store_true", help="Mostra progresso.")
    return p.parse_args()


class BackupRunner:
    def __init__(self, config_path: Path, *, resume: bool, premis_log: str | None, agent: str, progress: bool):
        self.config_path = config_path.resolve()
        self.plan = load_plan(self.config_path)
        self.name = plan_name(self.plan, self.config_path)
        self.dest = destination(self.plan)
        self.opts = options(self.plan)
        self.algo = str(self.opts.get("algo") or self.opts.get("algorithm") or "sha256").lower()
        self.ignore_hidden = bool(self.opts.get("ignore_hidden") or self.opts.get("ignorar_ocultos"))
        self.follow_symlinks = bool(self.opts.get("follow_symlinks") or self.opts.get("seguir_symlinks"))
        self.resume = resume
        self.progress = progress
        self.agent = agent
        self.run_id = run_id()
        self.tb = self.dest / "thor-backup"
        self.state_path = self.tb / "checkpoints" / f"{self.name}.state.json"
        self.stop_path = self.tb / "checkpoints" / "STOP"
        self.sources: list[dict[str, str]] = []
        self.manifests_dir = self.tb / "manifests"
        self.premis_log = Path(premis_log).resolve() if premis_log else self.tb / "logs" / "premis_events.jsonl"
        self.state: dict[str, Any] = {}
        self.report_rows: list[dict[str, Any]] = []
        self.completed: set[str] = set()
        self.prepared = False

    def emit(self, event_type: str, detail: str, outcome: str = "success") -> None:
        append_premis(self.premis_log, event_type, str(self.dest), detail, outcome, self.agent)

    def log(self, msg: str) -> None:
        if self.progress:
            print(msg)

    def save_state(self, status: str, extra: dict[str, Any] | None = None) -> None:
        self.state.update(
            {
                "backup": self.name,
                "run_id": self.run_id,
                "status": status,
                "destination": str(self.dest),
                "layout_version": 2,
                "algorithm": self.algo,
                "sources": self.sources,
                "manifests": {s["name"]: str(source_manifest_path(self.dest, s["name"], self.algo)) for s in self.sources},
                "updated_at": self.run_id,
                "completed": sorted(self.completed),
                "summary": self.summary(),
            }
        )
        if extra:
            self.state.update(extra)
        write_json(self.state_path, self.state)

    def summary(self) -> dict[str, int]:
        out = {"new": 0, "changed": 0, "same": 0, "removed": 0, "copied": 0, "versioned": 0, "failed": 0}
        for row in self.report_rows:
            st = row.get("status")
            if st in out:
                out[st] += 1
            if st in ("new", "changed"):
                out["copied"] += 1
            if st == "changed":
                out["versioned"] += 1
        return out

    def prepare(self) -> None:
        if self.algo not in hashlib.algorithms_available:
            raise ValueError(f"Algoritmo não suportado: {self.algo}")
        self.sources = normalize_sources(self.plan)
        validate_source_paths(self.dest, self.sources)
        if any(self.dest.glob("manifest-*.txt")):
            raise ValueError("Destino com estrutura anterior incompatível. Escolha um novo destino; os arquivos existentes não serão convertidos.")
        checkpoint = read_json(self.state_path) if self.resume else {}
        if self.resume:
            if not checkpoint:
                raise RuntimeError(f"Checkpoint não encontrado para retomada: {self.state_path}")
            if checkpoint.get("layout_version") != 2 or checkpoint.get("algorithm") != self.algo or checkpoint.get("sources") != self.sources:
                raise RuntimeError("Checkpoint incompatível com a estrutura, algoritmo ou origens do plano.")
            if checkpoint.get("destination") != str(self.dest) or checkpoint.get("status") not in {"RUNNING", "PAUSED", "FAILED"}:
                raise RuntimeError("Checkpoint não corresponde a uma execução interrompida neste destino.")
            for path in checkpoint.get("manifests", {}).values():
                if not Path(path).is_file():
                    raise RuntimeError(f"Manifesto do checkpoint não existe: {path}")
        ensure_repository(self.dest, self.algo, self.sources)
        self.prepared = True
        shutil.copy2(self.config_path, self.tb / "configs" / f"{self.name}_{self.run_id}.json")
        if self.resume:
            self.state = checkpoint
            self.completed = set(str(x) for x in self.state.get("completed", []))
            self.emit("BACKUP_RESUMED", f"Retomada com {len(self.completed)} arquivo(s) concluído(s).")
        else:
            self.state = {}
            self.completed = set()
            self.emit("BACKUP_STARTED", f"Backup iniciado pelo plano {self.config_path}.")
        self.save_state("RUNNING")

    def source_for_payload_path(self, payload_path: str, sources: list[dict[str, str]]) -> Path:
        for source in sources:
            prefix = f"{source['name']}/"
            if payload_path.startswith(prefix):
                rel = payload_path[len(prefix):]
                return Path(source["path"]).resolve() / Path(rel)
        raise RuntimeError(f"Não foi possível resolver origem para {payload_path}")

    def version_existing(self, payload_path: str) -> str:
        current = self.dest / Path(payload_path)
        if not current.exists():
            return ""
        version_target = self.tb / "versoes" / self.run_id / payload_path
        version_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(version_target))
        return str(version_target)

    def apply_changes(self, diff: dict[str, list[str]], source_entries: dict[str, str], sources: list[dict[str, str]]) -> dict[str, str]:
        dest_entries = read_source_manifests(self.dest, self.algo)
        updated = dict(dest_entries)
        work = [("same", p) for p in diff["same"]] + [("new", p) for p in diff["new"]] + [("changed", p) for p in diff["changed"]]
        total = len(work)
        marks = progress_marks(total) if total else []
        next_mark = 0
        started_at = time.perf_counter()
        if self.progress:
            print(f"[INFO] Itens a processar no backup: {total}")

        for idx, (status, payload_path) in enumerate(work, 1):
            self.state["pasta_em_processamento"] = payload_path.split("/", 1)[0]
            self.state["ultimo_arquivo_concluido"] = None
            self.save_state("RUNNING")

            try:
                if status == "same":
                    self.report_rows.append({"path": payload_path, "status": "same", "digest_after": source_entries[payload_path]})
                    self.completed.add(payload_path)
                else:
                    src = self.source_for_payload_path(payload_path, sources)
                    dst = self.dest / Path(payload_path)
                    old_digest = updated.get(payload_path, "")
                    detail = ""
                    if status == "changed":
                        version_path = self.version_existing(payload_path)
                        detail = f"Versão anterior preservada em {version_path}" if version_path else "Versão anterior não encontrada no disco."
                    copy_file(src, dst)
                    copied_digest = digest_file(dst, self.algo)
                    if copied_digest != source_entries[payload_path]:
                        raise RuntimeError(f"Hash divergente após cópia: {payload_path}")
                    updated[payload_path] = copied_digest
                    self.report_rows.append(
                        {
                            "path": payload_path,
                            "status": status,
                            "source": str(src),
                            "destination": str(dst),
                            "digest_before": old_digest,
                            "digest_after": copied_digest,
                            "detail": detail,
                        }
                    )
                    write_source_manifests(self.manifests_dir, updated, self.algo, (s["name"] for s in sources))
                self.completed.add(payload_path)
                self.state["ultimo_arquivo_concluido"] = payload_path
                if self.progress:
                    next_mark = emit_progress(idx, total, marks, next_mark, "Backup")
                self.save_state("RUNNING")
            except Exception as e:
                self.report_rows.append({"path": payload_path, "status": "failed", "detail": str(e)})
                self.save_state("FAILED", {"ultimo_erro": str(e)})
                raise

            if self.stop_path.exists():
                write_source_manifests(self.manifests_dir, updated, self.algo, (s["name"] for s in sources))
                self.save_state("PAUSED", {"ultimo_arquivo_concluido": payload_path})
                self.emit("BACKUP_PAUSED", f"Parada segura solicitada em {payload_path}.", "warning")
                raise StopRequested()

        for payload_path in diff["removed"]:
            self.report_rows.append(
                {
                    "path": payload_path,
                    "status": "removed",
                    "digest_before": dest_entries.get(payload_path, ""),
                    "detail": "Ausente na origem; preservado no backup e mantido no manifesto.",
                }
            )
            updated[payload_path] = dest_entries[payload_path]
        if self.progress:
            elapsed = time.perf_counter() - started_at
            avg = elapsed / total if total else 0.0
            print(
                f"[INFO] Backup finalizado: {total} item(ns) processado(s) em "
                f"{elapsed:.2f}s; média {avg:.4f}s/item"
            )
        return updated

    def run(self) -> int:
        started_at = time.perf_counter()
        try:
            self.prepare()
            sources = self.sources
            source_entries: dict[str, str] = {}

            for source in sources:
                root = Path(source["path"]).resolve()
                if not root.exists() or not root.is_dir():
                    raise RuntimeError(f"Origem inválida: {root}")
                prefix = source["name"]
                entries = build_manifest(
                    root,
                    prefix=prefix,
                    algo=self.algo,
                    ignore_hidden=self.ignore_hidden,
                    follow_symlinks=self.follow_symlinks,
                    progress=self.progress,
                )
                source_entries.update(entries)
            previous_entries = read_source_manifests(self.dest, self.algo)

            diff = diff_manifests(source_entries, previous_entries)
            history_dir = self.tb / "historico" / self.run_id
            diff_path = history_dir / "alteracoes.json"
            write_json(diff_path, diff)
            if previous_entries:
                self.emit("BACKUP_INCREMENTAL", f"Comparação incremental: {json.dumps({k: len(v) for k, v in diff.items()}, ensure_ascii=False)}")

            updated_entries = self.apply_changes(diff, source_entries, sources)
            names = [s["name"] for s in sources]
            write_source_manifests(self.manifests_dir, updated_entries, self.algo, names)
            write_source_manifests(history_dir, updated_entries, self.algo, names)

            elapsed = time.perf_counter() - started_at
            report_path = self.tb / "relatorios" / f"{self.name}_{self.run_id}_relatorio.txt"
            write_backup_report(
                report_path, self.report_rows, name=self.name, execution=self.run_id,
                config=self.config_path, dest=self.dest, algo=self.algo,
                sources=sources, elapsed=elapsed, resumed=self.resume,
            )
            self.save_state(
                "COMPLETED",
                {
                    "historico": str(history_dir),
                    "relatorio": str(report_path),
                },
            )
            self.emit("BACKUP_COMPLETED", f"Backup concluído. Relatório: {report_path}.")
            print(f"Backup concluído: {self.dest}")
            print("=== Resumo final do backup ===")
            for line in backup_report_summary(self.report_rows, elapsed):
                print(line)
            print(f"Relatório completo: {report_path}")
            return 0
        except StopRequested:
            print("Backup pausado por STOP.")
            return 0
        except Exception as e:
            if self.prepared:
                self.emit("BACKUP_FAILED", str(e), "failure")
                self.save_state("FAILED", {"ultimo_erro": str(e)})
            print(f"ERRO: {e}", file=sys.stderr)
            return 2


class StopRequested(Exception):
    pass


def main() -> int:
    args = parse_args()
    runner = BackupRunner(
        Path(args.config),
        resume=args.resume,
        premis_log=args.premis_log,
        agent=args.agent,
        progress=args.progress,
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
