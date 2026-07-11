from __future__ import annotations

import html
import sys
import time
import traceback
import unittest
from datetime import datetime
from pathlib import Path

from backup_test_metadata import TEST_METADATA


ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "tests" / "reports" / "backup_tests_report.html"


class HtmlResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def startTest(self, test):
        self._started_at = time.perf_counter()
        super().startTest(test)

    def _duration(self):
        return time.perf_counter() - getattr(self, "_started_at", time.perf_counter())

    def _record(self, test, status, detail=""):
        meta = TEST_METADATA.get(test.id(), {})
        self.records.append(
            {
                "test": self.getDescription(test),
                "test_id": test.id(),
                "status": status,
                "duration": self._duration(),
                "detail": detail,
                "purpose": meta.get("purpose", ""),
                "preconditions": meta.get("preconditions", ""),
                "postconditions": meta.get("postconditions", ""),
            }
        )

    def addSuccess(self, test):
        super().addSuccess(test)
        self._record(test, "PASS")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._record(test, "FAIL", self._exc_info_to_string(err, test))

    def addError(self, test, err):
        super().addError(test, err)
        self._record(test, "ERROR", self._exc_info_to_string(err, test))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._record(test, "SKIP", reason)

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self._record(test, "EXPECTED_FAILURE", self._exc_info_to_string(err, test))

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._record(test, "UNEXPECTED_SUCCESS")


class HtmlRunner(unittest.TextTestRunner):
    resultclass = HtmlResult


def status_class(status: str) -> str:
    if status == "PASS":
        return "pass"
    if status == "SKIP":
        return "skip"
    return "fail"


def write_report(result: HtmlResult, elapsed: float) -> None:
    counts = {
        "pass": sum(1 for r in result.records if r["status"] == "PASS"),
        "fail": len(result.failures),
        "error": len(result.errors),
        "skip": len(result.skipped),
        "total": result.testsRun,
    }
    rows = []
    list_items = []
    for index, record in enumerate(result.records, 1):
        detail = html.escape(record["detail"])
        if detail:
            detail = f"<pre>{detail}</pre>"
        list_items.append(
            "    <li>"
            f"<span class=\"{status_class(record['status'])}\">{html.escape(record['status'])}</span> - "
            f"{html.escape(record['test'])}"
            "</li>"
        )
        rows.append(
            "      <tr>\n"
            f"        <td>{index}</td>\n"
            f"        <td>{html.escape(record['test'])}</td>\n"
            f"        <td>{html.escape(record['purpose'])}</td>\n"
            f"        <td>{html.escape(record['preconditions'])}</td>\n"
            f"        <td>{html.escape(record['postconditions'])}</td>\n"
            f"        <td class=\"{status_class(record['status'])}\">{html.escape(record['status'])}</td>\n"
            f"        <td>{record['duration']:.3f}s</td>\n"
            f"        <td>{detail}</td>\n"
            "      </tr>"
        )

    generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ok = not result.failures and not result.errors and not result.unexpectedSuccesses
    css = """
body { font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #1f2937; }
h1 { margin-bottom: 4px; }
.summary { display: flex; gap: 12px; margin: 18px 0; flex-wrap: wrap; }
.card { border: 1px solid #d1d5db; border-radius: 6px; padding: 10px 14px; min-width: 110px; }
.status-ok { color: #047857; font-weight: 700; }
.status-bad { color: #b91c1c; font-weight: 700; }
table { width: 100%; border-collapse: collapse; margin-top: 14px; }
th, td { border: 1px solid #d1d5db; padding: 8px; vertical-align: top; text-align: left; }
th { background: #f3f4f6; }
ol.tests-list { line-height: 1.55; padding-left: 28px; }
.pass { color: #047857; font-weight: 700; }
.fail { color: #b91c1c; font-weight: 700; }
.skip { color: #92400e; font-weight: 700; }
pre { white-space: pre-wrap; margin: 0; font-size: 12px; }
"""
    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Relatório de Testes - Backup Preservacional</title>
  <style>{css}</style>
</head>
<body>
  <h1>Relatório de Testes - Backup Preservacional</h1>
  <div>Gerado em {html.escape(generated)}</div>
  <div class="{'status-ok' if ok else 'status-bad'}">Resultado: {'OK' if ok else 'FALHOU'}</div>
  <div class="summary">
    <div class="card"><strong>Total</strong><br>{counts['total']}</div>
    <div class="card"><strong>Passou</strong><br>{counts['pass']}</div>
    <div class="card"><strong>Falhas</strong><br>{counts['fail']}</div>
    <div class="card"><strong>Erros</strong><br>{counts['error']}</div>
    <div class="card"><strong>Ignorados</strong><br>{counts['skip']}</div>
    <div class="card"><strong>Duração</strong><br>{elapsed:.3f}s</div>
  </div>
  <h2>Lista de Testes Executados</h2>
  <ol class="tests-list">
{chr(10).join(list_items)}
  </ol>
  <h2>Detalhamento</h2>
  <table>
    <thead>
      <tr>
        <th>Nº</th>
        <th>Teste</th>
        <th>Finalidade</th>
        <th>Pré-condições</th>
        <th>Pós-condições</th>
        <th>Status</th>
        <th>Duração</th>
        <th>Detalhes</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(doc, encoding="utf-8")


def main() -> int:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test*.py")
    start = time.perf_counter()
    result = HtmlRunner(verbosity=2).run(suite)
    elapsed = time.perf_counter() - start
    try:
        write_report(result, elapsed)
        print(f"\nRelatório HTML: {REPORT}")
    except Exception:
        traceback.print_exc()
        return 2
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
