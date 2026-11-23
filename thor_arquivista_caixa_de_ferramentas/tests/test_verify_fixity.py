from __future__ import annotations

import hashlib
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from scripts import verify_fixity as vf


class VerifyFixityTests(unittest.TestCase):
    def test_extended_windows_paths(self):
        self.assertEqual(vf.io_path(r"\\server\share\ação\file.txt", windows=True),
                         r"\\?\UNC\server\share\ação\file.txt")
        self.assertEqual(vf.io_path(r"C:\ação\file.txt", windows=True),
                         r"\\?\C:\ação\file.txt")
        self.assertEqual(vf.io_path(r"\\?\UNC\server\share\file.txt", windows=True),
                         r"\\?\UNC\server\share\file.txt")

    def test_transient_read_failure_retries_entire_hash(self):
        with patch.object(vf, "hash_file", side_effect=[OSError(5, "I/O"), "abc"]) as read:
            with patch.object(vf.time, "sleep"):
                result = vf.check_entry(Path("."), ("abc", "file.txt"), "sha256")
        self.assertEqual(result[1], "OK")
        self.assertEqual(read.call_count, 2)

    def test_missing_is_retried_and_access_errors_are_not_missing(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(vf.time, "sleep"):
            with patch.object(vf, "hash_file", side_effect=FileNotFoundError(2, "missing")) as read:
                result = vf.check_entry(Path(tmp), ("abc", "missing.txt"), "sha256")
                self.assertEqual(result[1], "MISSING")
                self.assertEqual(read.call_count, 3)
            for exc in (PermissionError(13, "denied"), OSError(36, "name too long"), OSError(5, "network I/O")):
                with self.subTest(exc=exc), patch.object(vf, "hash_file", side_effect=exc):
                    result = vf.check_entry(Path(tmp), ("abc", "file.txt"), "sha256")
                    self.assertEqual(result[1], "ERROR")
                    self.assertIn("caracteres=", result[4])

    def test_windows_network_not_found_is_error(self):
        exc = FileNotFoundError(2, "network path unavailable")
        exc.winerror = 53
        with patch.object(vf, "hash_file", side_effect=exc), patch.object(vf.time, "sleep"):
            self.assertEqual(vf.check_entry(Path("."), ("abc", "file"), "sha256")[1], "ERROR")

    def test_missing_with_unavailable_root_is_error(self):
        with patch.object(vf, "hash_file", side_effect=FileNotFoundError(2, "missing")), \
             patch.object(vf.os, "stat", side_effect=OSError(5, "network")), \
             patch.object(vf.time, "sleep"):
            self.assertEqual(vf.check_entry(Path("."), ("abc", "file"), "sha256")[1], "ERROR")

    def run_verification(self, root, manifest, report):
        with patch("sys.argv", ["verify_fixity", "--raiz", str(root), "--manifesto", str(manifest),
                                "--report-file", str(report), "--workers", "1"]), \
             redirect_stdout(StringIO()), redirect_stderr(StringIO()), patch.object(vf.time, "sleep"):
            return vf.main()

    def test_report_separates_corruption_missing_and_access_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            root.mkdir()
            (root / "good").write_bytes(b"good")
            (root / "bad").write_bytes(b"bad")
            (root / "denied").write_bytes(b"denied")
            manifest = Path(tmp) / "manifest-sha256.txt"
            report = Path(tmp) / "report.txt"
            digest = hashlib.sha256(b"good").hexdigest()
            manifest.write_text("".join(f"{digest}  {name}\n" for name in ["good", "bad", "denied", "missing"]), encoding="utf-8")
            real_hash = vf.hash_file

            def read(path, algo):
                if path.name == "denied":
                    raise PermissionError(13, "denied")
                return real_hash(path, algo)

            with patch.object(vf, "hash_file", side_effect=read):
                self.assertEqual(self.run_verification(root, manifest, report), 1)
            text = report.read_text(encoding="utf-8")
            self.assertIn("Arquivos verificados íntegros: 1", text)
            self.assertIn("Arquivos verificados corrompidos: 1", text)
            self.assertIn("Erros de acesso ou leitura: 1", text)
            self.assertIn("ausentes na pasta analisada: 1", text)
            self.assertIn("ERROR\tdenied\t", text)
            self.assertIn("MISSING\tmissing\t", text)

    def test_directory_scan_failure_is_reported_and_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "data"
            root.mkdir()
            (root / "good").write_bytes(b"good")
            manifest = Path(tmp) / "manifest-sha256.txt"
            report = Path(tmp) / "report.txt"
            manifest.write_text(hashlib.sha256(b"good").hexdigest() + "  good\n", encoding="utf-8")

            def broken_walk(path, onerror):
                onerror(PermissionError(13, "directory denied"))
                return iter(())

            with patch.object(vf.os, "walk", side_effect=broken_walk):
                self.assertEqual(self.run_verification(root, manifest, report), 1)
            text = report.read_text(encoding="utf-8")
            self.assertIn("Busca de extras incompleta", text)
            self.assertIn("Busca de extras: incompleta", text)
            self.assertIn("SCAN_ERROR\t.\t", text)
            self.assertNotIn("\nERROR\t.\t", text)

    @unittest.skipUnless(os.name == "nt", "Windows long-path integration")
    def test_actual_long_path_with_accents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / ("ação" * 20) / ("exposição" * 10) / ("difusão" * 10)
            os.makedirs(vf.io_path(folder))
            target = folder / "documento.txt"
            self.assertGreater(len(str(target)), 260)
            with open(vf.io_path(target), "wb") as stream:
                stream.write(b"preserved")
            digest = hashlib.sha256(b"preserved").hexdigest()
            manifest = root / "manifest-sha256.txt"
            manifest.write_text(f"{digest}  {target.relative_to(root).as_posix()}\n", encoding="utf-8")
            self.assertEqual(self.run_verification(root, manifest, root / "report.txt"), 0)


if __name__ == "__main__":
    unittest.main()
