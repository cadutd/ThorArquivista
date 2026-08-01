from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import hashlib
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from scripts.backup_common import read_manifest, write_json
from scripts.backup_manifest_build import build_manifest
from scripts.backup_manifest_diff import diff_manifests
from scripts.backup_plan import BackupRunner
from scripts.backup_verify import main as verify_main
from scripts.build_bag import build_bag
from scripts.incremental_backup_from_fixity import main as incremental_backup_fixity_main
from scripts.validate_bag import main as validate_bag_main
from scripts.verify_fixity import main as verify_fixity_main


class PreservationBackupScriptTests(unittest.TestCase):
    def make_plan(self, root: Path, *, options=None, sources=None) -> Path:
        source = root / "src"
        source.mkdir(exist_ok=True)
        plan = {
            "name": "backup_teste",
            "destination": str(root / "Backup"),
            "sources": sources or [{"name": "origem", "path": str(source)}],
            "options": options or {"algo": "sha256"},
        }
        plan_path = root / "backup.json"
        write_json(plan_path, plan)
        return plan_path

    def run_backup(self, plan_path: Path, *, resume=False, premis_log=None) -> int:
        runner = BackupRunner(plan_path, resume=resume, premis_log=str(premis_log) if premis_log else None, agent="tests", progress=False)
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            return runner.run()

    def test_manifest_build_covers_prefix_hidden_and_hash_algorithm(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "visible.txt").write_text("visible", encoding="utf-8")
            (root / ".hidden.txt").write_text("hidden", encoding="utf-8")

            entries = build_manifest(root, prefix="data/origem", algo="sha512", ignore_hidden=True)

            self.assertIn("data/origem/visible.txt", entries)
            self.assertNotIn("data/origem/.hidden.txt", entries)
            self.assertEqual(len(entries["data/origem/visible.txt"]), 128)

    def test_manifest_build_follow_symlinks_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.txt"
            target.write_text("target", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink indisponível neste ambiente.")

            no_follow = build_manifest(root, prefix="data/origem", follow_symlinks=False)
            follow = build_manifest(root, prefix="data/origem", follow_symlinks=True)

            self.assertNotIn("data/origem/link.txt", no_follow)
            self.assertIn("data/origem/link.txt", follow)

    def test_manifest_diff_covers_new_changed_same_and_removed(self):
        source = {"a": "1", "b": "2", "c": "3"}
        destination = {"b": "old", "c": "3", "d": "4"}

        diff = diff_manifests(source, destination)

        self.assertEqual(diff["new"], ["a"])
        self.assertEqual(diff["changed"], ["b"])
        self.assertEqual(diff["same"], ["c"])
        self.assertEqual(diff["removed"], ["d"])

    def test_backup_runner_creates_bagit_repository_and_premis_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            premis = root / "premis.jsonl"
            plan = self.make_plan(root)

            rc = self.run_backup(plan, premis_log=premis)

            self.assertEqual(rc, 0)
            dest = root / "Backup"
            self.assertTrue((dest / "bagit.txt").exists())
            self.assertTrue((dest / "bag-info.txt").exists())
            self.assertTrue((dest / "tagmanifest-sha256.txt").exists())
            self.assertEqual((dest / "data" / "origem" / "a.txt").read_text(encoding="utf-8"), "alpha")
            manifest = read_manifest(dest / "manifest-sha256.txt")
            self.assertIn("data/origem/a.txt", manifest)
            events = [json.loads(line)["eventType"] for line in premis.read_text(encoding="utf-8").splitlines()]
            self.assertIn("BACKUP_STARTED", events)
            self.assertIn("BACKUP_COMPLETED", events)

    def test_backup_runner_incremental_versions_changed_and_preserves_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            (source / "remove.txt").write_text("keep old", encoding="utf-8")
            plan = self.make_plan(root)
            self.assertEqual(self.run_backup(plan), 0)

            (source / "a.txt").write_text("alpha changed", encoding="utf-8")
            (source / "remove.txt").unlink()
            self.assertEqual(self.run_backup(plan), 0)

            dest = root / "Backup"
            self.assertEqual((dest / "data" / "origem" / "a.txt").read_text(encoding="utf-8"), "alpha changed")
            self.assertTrue((dest / "data" / "origem" / "remove.txt").exists())
            versions = list((dest / "thor-backup" / "versoes").rglob("a.txt"))
            self.assertEqual(len(versions), 1)
            self.assertEqual(versions[0].read_text(encoding="utf-8"), "alpha")
            manifest = read_manifest(dest / "manifest-sha256.txt")
            self.assertIn("data/origem/remove.txt", manifest)

    def test_backup_runner_pause_and_resume_via_stop_checkpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            plan = self.make_plan(root)
            dest = root / "Backup"
            stop = dest / "thor-backup" / "checkpoints" / "STOP"
            stop.parent.mkdir(parents=True)
            stop.write_text("STOP\n", encoding="utf-8")

            self.assertEqual(self.run_backup(plan), 0)
            state = json.loads((dest / "thor-backup" / "checkpoints" / "backup_teste.state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "PAUSED")

            stop.unlink()
            self.assertEqual(self.run_backup(plan, resume=True), 0)
            state = json.loads((dest / "thor-backup" / "checkpoints" / "backup_teste.state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "COMPLETED")

    def test_backup_runner_options_ignore_hidden_and_sha512(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            (source / ".hidden.txt").write_text("hidden", encoding="utf-8")
            plan = self.make_plan(root, options={"algo": "sha512", "ignore_hidden": True, "follow_symlinks": False})

            self.assertEqual(self.run_backup(plan), 0)
            dest = root / "Backup"
            self.assertTrue((dest / "manifest-sha512.txt").exists())
            manifest = read_manifest(dest / "manifest-sha512.txt")
            self.assertIn("data/origem/a.txt", manifest)
            self.assertNotIn("data/origem/.hidden.txt", manifest)
            self.assertEqual(len(manifest["data/origem/a.txt"]), 128)

    def test_backup_runner_reports_failure_for_invalid_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing"
            plan = self.make_plan(root, sources=[{"name": "origem", "path": str(missing)}])

            rc = self.run_backup(plan)

            self.assertEqual(rc, 2)
            state_path = root / "Backup" / "thor-backup" / "checkpoints" / "backup_teste.state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["status"], "FAILED")

    def test_backup_verify_records_fixity_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "src"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            plan = self.make_plan(root)
            self.assertEqual(self.run_backup(plan), 0)
            premis = root / "verify.jsonl"

            import sys
            old_argv = sys.argv
            try:
                sys.argv = ["backup_verify.py", "--destino", str(root / "Backup"), "--premis-log", str(premis)]
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    rc = verify_main()
            finally:
                sys.argv = old_argv

            self.assertEqual(rc, 0)
            event = json.loads(premis.read_text(encoding="utf-8").splitlines()[-1])
            self.assertEqual(event["eventType"], "FIXITY_CHECK")
            self.assertEqual(event["eventOutcome"], "success")

    def test_validate_bag_accepts_package_created_by_build_bag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            (source / "sub").mkdir()
            (source / "sub" / "b.txt").write_text("beta", encoding="utf-8")
            bag = root / "bag"

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                build_bag(source, bag, algo="sha256", tagmanifest=True)

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = ["validate_bag.py", str(bag)]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = validate_bag_main()
            finally:
                sys.argv = old_argv

            text = out.getvalue()
            self.assertEqual(rc, 0)
            self.assertIn("Resultado: VÁLIDO", text)
            self.assertIn("Arquivos de payload verificados íntegros: 2", text)
            self.assertIn("Arquivos extras em data/ ausentes nos manifestos: 0", text)
            self.assertIn("Arquivos de tag verificados íntegros: 3", text)

    def test_validate_bag_reports_corrupt_and_extra_payload_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            bag = root / "bag"

            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                build_bag(source, bag, algo="sha256")

            (bag / "data" / "a.txt").write_text("changed", encoding="utf-8")
            (bag / "data" / "extra.txt").write_text("extra", encoding="utf-8")

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = ["validate_bag.py", str(bag)]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = validate_bag_main()
            finally:
                sys.argv = old_argv

            text = out.getvalue()
            self.assertEqual(rc, 2)
            self.assertIn("Resultado: INVÁLIDO", text)
            self.assertIn("Arquivos de payload verificados corrompidos: 1", text)
            self.assertIn("Arquivos extras em data/ ausentes nos manifestos: 1", text)
            self.assertIn("data/a.txt :: MISMATCH", text)
            self.assertIn("data/extra.txt", text)

    def test_verify_fixity_report_lists_integrity_missing_and_extra_counts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok = root / "ok.txt"
            bad = root / "bad.txt"
            extra = root / "extra.txt"
            manifest = root / "manifest-sha256.txt"
            ok.write_text("ok", encoding="utf-8")
            bad.write_text("original", encoding="utf-8")
            extra.write_text("extra", encoding="utf-8")

            ok_hash = hashlib.sha256(ok.read_bytes()).hexdigest()
            bad_hash = hashlib.sha256(bad.read_bytes()).hexdigest()
            manifest.write_text(
                f"{ok_hash}  ok.txt\n"
                f"{bad_hash}  bad.txt\n"
                f"{ok_hash}  missing.txt\n",
                encoding="utf-8",
            )
            bad.write_text("changed", encoding="utf-8")

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = [
                    "verify_fixity.py",
                    "--raiz",
                    str(root),
                    "--manifesto",
                    str(manifest),
                    "--report-extras",
                ]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = verify_fixity_main()
            finally:
                sys.argv = old_argv

            text = out.getvalue()
            self.assertEqual(rc, 1)
            self.assertIn("Arquivos verificados íntegros: 1", text)
            self.assertIn("Arquivos verificados corrompidos: 1", text)
            self.assertIn("Arquivos no manifesto ausentes na pasta analisada: 1", text)
            self.assertIn("Arquivos na pasta analisada ausentes no manifesto: 1", text)
            self.assertIn("Arquivos na pasta analisada ausentes no manifesto:", text)
            self.assertIn("missing.txt", text)
            self.assertIn("bad.txt :: MISMATCH", text)
            self.assertIn("extra.txt", text)
            self.assertNotIn("\nmanifest-sha256.txt\n", text)

    def test_verify_fixity_report_shows_zero_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ok = root / "ok.txt"
            manifest = root / "manifest-sha256.txt"
            report = root / "fixity_ok_report.txt"
            ok.write_text("ok", encoding="utf-8")
            ok_hash = hashlib.sha256(ok.read_bytes()).hexdigest()
            manifest.write_text(f"{ok_hash}  ok.txt\n", encoding="utf-8")

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = [
                    "verify_fixity.py",
                    "--raiz",
                    str(root),
                    "--manifesto",
                    str(manifest),
                    "--report-file",
                    str(report),
                ]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = verify_fixity_main()
            finally:
                sys.argv = old_argv

            text = out.getvalue()
            report_text = report.read_text(encoding="utf-8")
            self.assertEqual(rc, 0)
            self.assertIn("Arquivos verificados íntegros: 1", text)
            self.assertIn("Arquivos verificados corrompidos: 0", text)
            self.assertIn("Arquivos no manifesto ausentes na pasta analisada: 0", text)
            self.assertIn("Arquivos na pasta analisada ausentes no manifesto: 0", text)
            self.assertIn("-- Arquivos no manifesto ausentes na pasta analisada --\nNenhum", text)
            self.assertIn("-- Arquivos verificados corrompidos ou com erro --\nNenhum", text)
            self.assertIn("-- Arquivos na pasta analisada ausentes no manifesto --\nNenhum", text)
            self.assertIn("Relatório completo:", text)
            self.assertIn("=== Dados estruturados para backup incremental ===", report_text)
            self.assertIn("status\tpath\texpected_hash\tactual_hash\tdetail", report_text)
            self.assertIn(f"OK\tok.txt\t{ok_hash}\t{ok_hash}\t", report_text)

    def test_verify_fixity_large_lists_are_capped_in_stdout_and_written_to_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "manifest-sha256.txt"
            report = root / "fixity_report.txt"
            fake_hash = "0" * 64
            manifest.write_text(
                "".join(f"{fake_hash}  missing_{i}.txt\n" for i in range(5)),
                encoding="utf-8",
            )

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = [
                    "verify_fixity.py",
                    "--raiz",
                    str(root),
                    "--manifesto",
                    str(manifest),
                    "--max-list-items",
                    "2",
                    "--report-file",
                    str(report),
                ]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = verify_fixity_main()
            finally:
                sys.argv = old_argv

            text = out.getvalue()
            full = report.read_text(encoding="utf-8")
            self.assertEqual(rc, 1)
            self.assertIn("missing_0.txt", text)
            self.assertIn("missing_1.txt", text)
            self.assertIn("3 item(s) omitidos", text)
            self.assertIn(f"Relatório completo: {report}", text)
            self.assertNotIn("missing_4.txt", text)
            self.assertIn("missing_4.txt", full)
            self.assertIn("MISSING\tmissing_4.txt", full)

    def test_incremental_backup_from_fixity_copies_missing_and_corrupt_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            dest = root / "dest"
            source.mkdir()
            dest.mkdir()
            (source / "a.txt").write_text("alpha new", encoding="utf-8")
            (source / "b.txt").write_text("beta", encoding="utf-8")
            (source / "c.txt").write_text("gamma", encoding="utf-8")
            (dest / "a.txt").write_text("alpha old", encoding="utf-8")
            (dest / "extra.txt").write_text("extra", encoding="utf-8")
            fixity_report = root / "fixity.txt"
            apply_report = root / "apply.txt"
            fixity_report.write_text(
                "=== Dados estruturados para backup incremental ===\n"
                "# Formato: TSV\n"
                "status\tpath\texpected_hash\tactual_hash\tdetail\n"
                "CORRUPT\ta.txt\texpected\tactual\tHash divergente\n"
                "MISSING\tb.txt\texpected\t\tAusente\n"
                "ERROR\tc.txt\texpected\t\tErro de leitura\n"
                "EXTRA\textra.txt\t\t\tExtra\n"
                "OK\tok.txt\thash\thash\t\n",
                encoding="utf-8",
            )

            old_argv = sys.argv
            out = StringIO()
            try:
                sys.argv = [
                    "incremental_backup_from_fixity.py",
                    "--relatorio-fixidez",
                    str(fixity_report),
                    "--origem",
                    str(source),
                    "--destino",
                    str(dest),
                    "--saida-relatorio",
                    str(apply_report),
                ]
                with redirect_stdout(out), redirect_stderr(StringIO()):
                    rc = incremental_backup_fixity_main()
            finally:
                sys.argv = old_argv

            self.assertEqual(rc, 0)
            self.assertEqual((dest / "a.txt").read_text(encoding="utf-8"), "alpha new")
            self.assertEqual((dest / "b.txt").read_text(encoding="utf-8"), "beta")
            self.assertEqual((dest / "c.txt").read_text(encoding="utf-8"), "gamma")
            self.assertTrue((dest / "extra.txt").exists())
            report_text = apply_report.read_text(encoding="utf-8")
            self.assertIn("Arquivos copiados: 3", report_text)
            self.assertIn("Registros EXTRA ignorados: 1", report_text)

    def test_incremental_backup_from_fixity_dry_run_does_not_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            dest = root / "dest"
            source.mkdir()
            dest.mkdir()
            (source / "a.txt").write_text("alpha", encoding="utf-8")
            fixity_report = root / "fixity.txt"
            apply_report = root / "apply.txt"
            fixity_report.write_text(
                "status\tpath\texpected_hash\tactual_hash\tdetail\n"
                "MISSING\ta.txt\texpected\t\tAusente\n",
                encoding="utf-8",
            )

            old_argv = sys.argv
            try:
                sys.argv = [
                    "incremental_backup_from_fixity.py",
                    "--relatorio-fixidez",
                    str(fixity_report),
                    "--origem",
                    str(source),
                    "--destino",
                    str(dest),
                    "--saida-relatorio",
                    str(apply_report),
                    "--dry-run",
                ]
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    rc = incremental_backup_fixity_main()
            finally:
                sys.argv = old_argv

            self.assertEqual(rc, 0)
            self.assertFalse((dest / "a.txt").exists())
            self.assertIn("Modo simulação: sim", apply_report.read_text(encoding="utf-8"))

    def tearDown(self):
        # Defensive cleanup for Windows handles in case a test leaves a temp dir behind.
        pass


if __name__ == "__main__":
    unittest.main()
