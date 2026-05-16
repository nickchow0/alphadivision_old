"""Tests for backup.py."""
import os
import subprocess
import unittest
from unittest.mock import MagicMock, patch, call


class TestRunPgDump(unittest.TestCase):
    @patch("backup.backup.subprocess.run")
    def test_creates_compressed_backup_file(self, mock_run):
        import tempfile
        from backup.backup import run_pg_dump
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = b"-- PostgreSQL dump\nSELECT 1;\n"
        mock_run.return_value.stderr = b""

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.sql.gz")
            result = run_pg_dump("myuser", "alphadivision", output_path)

        self.assertTrue(result)
        mock_run.assert_called_once_with(
            ["docker", "compose", "exec", "-T", "postgres",
             "pg_dump", "-U", "myuser", "alphadivision"],
            cwd=unittest.mock.ANY,
            capture_output=True,
            timeout=300,
        )

    @patch("backup.backup.subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run):
        import tempfile
        from backup.backup import run_pg_dump
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = b""
        mock_run.return_value.stderr = b"error: connection refused"

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.sql.gz")
            result = run_pg_dump("myuser", "alphadivision", output_path)

        self.assertFalse(result)

    @patch("backup.backup.subprocess.run")
    def test_returns_false_on_exception(self, mock_run):
        import tempfile
        from backup.backup import run_pg_dump
        mock_run.side_effect = subprocess.TimeoutExpired(["docker"], 300)

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.sql.gz")
            result = run_pg_dump("myuser", "alphadivision", output_path)

        self.assertFalse(result)

    @patch("backup.backup.subprocess.run")
    def test_writes_gzipped_content(self, mock_run):
        import tempfile, gzip as gz
        from backup.backup import run_pg_dump
        sql_bytes = b"-- PostgreSQL dump\nSELECT 1;\n"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = sql_bytes
        mock_run.return_value.stderr = b""

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, "test.sql.gz")
            run_pg_dump("myuser", "alphadivision", output_path)
            with gz.open(output_path, "rb") as f:
                content = f.read()

        self.assertEqual(content, sql_bytes)


class TestUploadToOci(unittest.TestCase):
    @patch("backup.backup.subprocess.run")
    def test_calls_oci_put_with_correct_args(self, mock_run):
        from backup.backup import upload_to_oci
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = b""
        result = upload_to_oci("my-bucket", "my-namespace", "alphadivision-20260516.sql.gz", "/backups/alphadivision-20260516.sql.gz")
        self.assertTrue(result)
        mock_run.assert_called_once_with(
            [
                "oci", "os", "object", "put",
                "--bucket-name", "my-bucket",
                "--namespace", "my-namespace",
                "--name", "alphadivision-20260516.sql.gz",
                "--file", "/backups/alphadivision-20260516.sql.gz",
                "--force",
            ],
            capture_output=True,
            timeout=120,
        )

    @patch("backup.backup.subprocess.run")
    def test_returns_false_on_nonzero_exit(self, mock_run):
        from backup.backup import upload_to_oci
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = b"ServiceError"
        result = upload_to_oci("my-bucket", "my-namespace", "obj.sql.gz", "/backups/obj.sql.gz")
        self.assertFalse(result)

    @patch("backup.backup.subprocess.run")
    def test_returns_false_on_exception(self, mock_run):
        from backup.backup import upload_to_oci
        mock_run.side_effect = subprocess.TimeoutExpired(["oci"], 120)
        result = upload_to_oci("my-bucket", "my-namespace", "obj.sql.gz", "/backups/obj.sql.gz")
        self.assertFalse(result)


class TestPruneLocalBackups(unittest.TestCase):
    def _make_backup_files(self, tmpdir: str, names: list) -> list:
        paths = []
        for name in names:
            p = os.path.join(tmpdir, name)
            with open(p, "w") as f:
                f.write("dummy")
            paths.append(p)
        return paths

    def test_deletes_files_older_than_retention(self):
        import tempfile
        from backup.backup import prune_local_backups
        from datetime import date, timedelta

        today = date(2026, 5, 16)
        old_date = today - timedelta(days=31)
        keep_date = today - timedelta(days=10)

        with tempfile.TemporaryDirectory() as tmpdir:
            old_name = f"alphadivision-{old_date.strftime('%Y%m%d')}.sql.gz"
            keep_name = f"alphadivision-{keep_date.strftime('%Y%m%d')}.sql.gz"
            self._make_backup_files(tmpdir, [old_name, keep_name])

            deleted = prune_local_backups(tmpdir, retention_days=30, today=today)

        self.assertEqual(deleted, [old_name])

    def test_keeps_files_within_retention(self):
        import tempfile
        from backup.backup import prune_local_backups
        from datetime import date, timedelta

        today = date(2026, 5, 16)
        keep_date = today - timedelta(days=29)

        with tempfile.TemporaryDirectory() as tmpdir:
            keep_name = f"alphadivision-{keep_date.strftime('%Y%m%d')}.sql.gz"
            self._make_backup_files(tmpdir, [keep_name])

            deleted = prune_local_backups(tmpdir, retention_days=30, today=today)

        self.assertEqual(deleted, [])

    def test_ignores_non_backup_files(self):
        import tempfile
        from backup.backup import prune_local_backups
        from datetime import date

        today = date(2026, 5, 16)

        with tempfile.TemporaryDirectory() as tmpdir:
            self._make_backup_files(tmpdir, ["somefile.txt"])
            deleted = prune_local_backups(tmpdir, retention_days=30, today=today)

        self.assertEqual(deleted, [])

    def test_returns_empty_list_for_nonexistent_dir(self):
        from backup.backup import prune_local_backups
        from datetime import date
        deleted = prune_local_backups("/nonexistent/path", retention_days=30, today=date(2026, 5, 16))
        self.assertEqual(deleted, [])


if __name__ == "__main__":
    unittest.main()
