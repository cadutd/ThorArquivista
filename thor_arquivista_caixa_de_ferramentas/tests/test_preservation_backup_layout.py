from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from scripts.backup_common import normalize_sources, read_manifest, write_json
from scripts.backup_plan import BackupRunner
from ui.panels import preservation_backup
from core.config import AppConfig
from core.scripts_map import _args_backup_verify


class PreservationBackupLayoutTests(unittest.TestCase):
    def plan(self, root, algo="sha256"):
        sources = []
        for name in ("documentos", "imagens"):
            source = root / "origens" / name
            source.mkdir(parents=True)
            (source / "sub").mkdir()
            (source / "sub" / "arquivo.txt").write_text(name, encoding="utf-8")
            sources.append({"name": name, "path": str(source)})
        path = root / "plano.json"
        write_json(path, {"name": "acervo", "destination": str(root / "Backup"), "sources": sources, "options": {"algo": algo}})
        return path

    def run_backup(self, plan, resume=False):
        runner = BackupRunner(plan, resume=resume, premis_log=None, agent="tests", progress=False)
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            rc = runner.run()
        return rc, runner

    def verify(self, root, *args):
        return subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "backup_verify.py"), "--destino", str(root / "Backup"), *args],
            capture_output=True,
        )

    def test_two_origins_have_independent_relative_manifests_and_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            rc, runner = self.run_backup(plan)
            self.assertEqual(rc, 0)
            dest = root / "Backup"
            self.assertEqual({p.name for p in dest.iterdir()}, {"documentos", "imagens", "thor-backup"})
            for name in ("documentos", "imagens"):
                self.assertEqual((dest / name / "sub/arquivo.txt").read_text(encoding="utf-8"), name)
                expected = {"sub/arquivo.txt": hashlib.sha256(name.encode()).hexdigest()}
                self.assertEqual(read_manifest(dest / "thor-backup/manifests" / name / "manifest-sha256.txt"), expected)
                self.assertEqual(read_manifest(dest / "thor-backup/historico" / runner.run_id / name / "manifest-sha256.txt"), expected)
            history = dest / "thor-backup/historico" / runner.run_id
            self.assertTrue((history / "alteracoes.json").is_file())
            self.assertEqual(self.verify(root).returncode, 0)
            self.assertFalse(list((dest / "documentos").glob("verify*")))
            result = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/backup_report.py"), "--destino", str(dest)], capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertEqual(len(json.loads(result.stdout)["manifestos_historicos"]), 2)

    def test_verification_detects_all_origins_and_sha512_without_algorithm_argument(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root, "sha512")
            self.assertEqual(self.run_backup(plan)[0], 0)
            self.assertEqual(self.verify(root).returncode, 0)
            (root / "Backup/documentos/sub/arquivo.txt").write_text("corrompido", encoding="utf-8")
            (root / "Backup/imagens/sub/arquivo.txt").unlink()
            log = root / "verify.jsonl"
            result = self.verify(root, "--premis-log", str(log))
            self.assertNotEqual(result.returncode, 0)
            events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(events), 2)
            self.assertTrue(all(e["eventOutcome"] == "failure" for e in events))
            self.assertEqual(self.verify(root, "--algo", "md5").returncode, 2)

    def test_empty_origin_has_manifest_and_can_be_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            for name in ("documentos", "imagens"):
                (root / "origens" / name / "sub/arquivo.txt").unlink()
            self.assertEqual(self.run_backup(plan)[0], 0)
            for name in ("documentos", "imagens"):
                manifest = root / "Backup/thor-backup/manifests" / name / "manifest-sha256.txt"
                self.assertTrue(manifest.is_file())
                self.assertEqual(read_manifest(manifest), {})
            self.assertEqual(self.verify(root).returncode, 0)
            report = next((root / "Backup/thor-backup/relatorios").glob("*_relatorio.txt")).read_text(encoding="utf-8")
            self.assertIn("Total de arquivos no relatório: 0", report)
            self.assertIn("-- Arquivos novos copiados (0) --\nNenhum", report)
            self.assertIn("-- Arquivos com falha (0) --\nNenhum", report)

    def test_final_report_is_readable_and_matches_incremental_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            removed = root / "origens/documentos/removido.txt"
            removed.write_text("preservar", encoding="utf-8")
            self.assertEqual(self.run_backup(plan)[0], 0)
            removed.unlink()
            (root / "origens/documentos/sub/arquivo.txt").write_text("alterado", encoding="utf-8")
            (root / "origens/documentos/novo.txt").write_text("novo", encoding="utf-8")
            rc, runner = self.run_backup(plan)
            self.assertEqual(rc, 0)
            state = json.loads(runner.state_path.read_text(encoding="utf-8"))
            report_path = Path(state["relatorio"])
            self.assertEqual(report_path.suffix, ".txt")
            text = report_path.read_text(encoding="utf-8")
            for expected in (
                "=== Backup preservacional ===", "Resultado : CONCLUÍDO",
                "Retomada de checkpoint: não", "Origem: documentos", "Origem: imagens",
                "Total de arquivos no relatório: 4", "Arquivos novos copiados: 1",
                "Arquivos alterados copiados: 1", "Cópias com hash conferido: 2",
                "Arquivos iguais ao manifesto (sem nova cópia): 1",
                "Arquivos ausentes na origem e preservados no destino: 1",
                "-- Arquivos novos copiados (1) --\ndocumentos/novo.txt",
                "-- Arquivos alterados copiados (1) --\ndocumentos/sub/arquivo.txt",
                "-- Arquivos iguais ao manifesto (1) --\nimagens/sub/arquivo.txt",
                "-- Arquivos ausentes na origem e preservados no destino (1) --\ndocumentos/removido.txt",
                "-- Arquivos com falha (0) --\nNenhum",
                "=== Resumo final do backup ===", "Tempo total de execução:",
                hashlib.sha256(b"documentos").hexdigest(), hashlib.sha256(b"alterado").hexdigest(),
                "Versão anterior preservada em", str(root / "Backup/thor-backup/versoes"),
            ):
                self.assertIn(expected, text)
            self.assertFalse(list(report_path.parent.glob("*.csv")))
            events = [json.loads(line) for line in runner.premis_log.read_text(encoding="utf-8").splitlines()]
            self.assertIn(str(report_path), events[-1]["eventDetail"])

    def test_verification_fails_when_one_expected_manifest_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            self.assertEqual(self.run_backup(plan)[0], 0)
            (root / "Backup/thor-backup/manifests/imagens/manifest-sha256.txt").unlink()
            self.assertEqual(self.verify(root).returncode, 2)

    def test_stop_with_only_unchanged_files_and_resume_rechecks_changed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            self.assertEqual(self.run_backup(plan)[0], 0)
            stop = root / "Backup/thor-backup/checkpoints/STOP"
            stop.write_text("STOP", encoding="utf-8")
            rc, runner = self.run_backup(plan)
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(runner.state_path.read_text(encoding="utf-8"))["status"], "PAUSED")
            (root / "origens/documentos/sub/arquivo.txt").write_text("nova versão", encoding="utf-8")
            stop.unlink()
            self.assertEqual(self.run_backup(plan, resume=True)[0], 0)
            self.assertEqual((root / "Backup/documentos/sub/arquivo.txt").read_text(encoding="utf-8"), "nova versão")
            versions = list((root / "Backup/thor-backup/versoes").glob("*/documentos/sub/arquivo.txt"))
            self.assertEqual(len(versions), 1)
            self.assertEqual(versions[0].read_text(encoding="utf-8"), "documentos")

    def test_pause_and_resume_with_two_origins_preserves_completed_copies(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            stop = root / "Backup/thor-backup/checkpoints/STOP"
            stop.parent.mkdir(parents=True)
            stop.write_text("STOP", encoding="utf-8")
            rc, runner = self.run_backup(plan)
            self.assertEqual(rc, 0)
            self.assertEqual(json.loads(runner.state_path.read_text(encoding="utf-8"))["status"], "PAUSED")
            stop.unlink()
            self.assertEqual(self.run_backup(plan, resume=True)[0], 0)
            self.assertEqual(self.verify(root).returncode, 0)
            self.assertFalse(list((root / "Backup/thor-backup/versoes").rglob("*.txt")))

    def test_old_destination_and_checkpoint_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self.plan(root)
            dest = root / "Backup"
            dest.mkdir()
            legacy = dest / "manifest-sha256.txt"
            legacy.write_text("anterior", encoding="utf-8")
            checkpoint = dest / "thor-backup/checkpoints/acervo.state.json"
            write_json(checkpoint, {"status": "PAUSED", "manifest": str(legacy)})
            before = checkpoint.read_bytes()
            for resume in (False, True):
                self.assertEqual(self.run_backup(plan, resume)[0], 2)
                self.assertEqual(checkpoint.read_bytes(), before)
                self.assertEqual(legacy.read_text(encoding="utf-8"), "anterior")
                self.assertFalse((dest / "documentos").exists())

    def test_reserved_and_colliding_names_are_rejected(self):
        for names in (("thor-backup",), ("Docs", "docs"), ("meus docs", "meus/docs")):
            with self.subTest(names=names), self.assertRaises(ValueError):
                normalize_sources({"sources": [{"name": n, "path": "origem"} for n in names]})

    def test_destination_inside_source_is_rejected_without_creating_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "plano.json"
            dest = root / "Backup"
            write_json(plan, {"destination": str(dest), "sources": [{"name": "docs", "path": str(root)}]})
            self.assertEqual(self.run_backup(plan)[0], 2)
            self.assertFalse(dest.exists())

    def test_gui_and_worker_leave_algorithm_detection_to_verifier(self):
        class Var:
            def get(self):
                return "E:/Backup"

        jobs = []
        with patch.object(preservation_backup.messagebox, "showinfo"):
            preservation_backup._enqueue_verify(lambda *job: jobs.append(job), Var(), None)
        self.assertEqual(jobs[0][0], "BACKUP_VERIFY")
        self.assertNotIn("algo", jobs[0][1])
        cfg = AppConfig()
        self.assertNotIn("--algo", _args_backup_verify(jobs[0][1], cfg))
        explicit = _args_backup_verify({"destino": "E:/Backup", "algo": "sha512"}, cfg)
        self.assertEqual(explicit[explicit.index("--algo") + 1], "sha512")


if __name__ == "__main__":
    unittest.main()
