from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
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

    def tearDown(self):
        # Defensive cleanup for Windows handles in case a test leaves a temp dir behind.
        pass


if __name__ == "__main__":
    unittest.main()
