from __future__ import annotations

import tempfile
import threading
import unittest
from pathlib import Path

from core.jobstore import JobStore


class JobStoreTests(unittest.TestCase):
    def test_multiple_instances_can_append_logs_to_same_file_concurrently(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "jobs_db.json"
            jobstore = JobStore(path)
            job_id = jobstore.add_job("VERIFY_FIXITY", {"manifesto": "manifest-sha256.txt"})

            def add_logs(worker_index: int) -> None:
                local_store = JobStore(path)
                for line_index in range(25):
                    local_store.add_log(job_id, f"worker={worker_index} line={line_index}")

            threads = [threading.Thread(target=add_logs, args=(index,)) for index in range(6)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

            logs = JobStore(path).get_logs(job_id)
            messages = [log["msg"] for log in logs]

            self.assertEqual(len(logs), 150)
            self.assertIn("worker=0 line=0", messages)
            self.assertIn("worker=5 line=24", messages)

    def test_bulk_logs_are_limited_per_job(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "jobs_db.json"
            jobstore = JobStore(path, max_logs_per_job=100)
            job_id = jobstore.add_job("VERIFY_FIXITY", {})

            jobstore.add_logs(job_id, [(f"line={index}", "INFO") for index in range(150)])

            logs = JobStore(path, max_logs_per_job=100).get_logs(job_id)
            messages = [log["msg"] for log in logs]

            self.assertEqual(len(logs), 100)
            self.assertEqual(messages[0], "line=50")
            self.assertEqual(messages[-1], "line=149")


if __name__ == "__main__":
    unittest.main()
