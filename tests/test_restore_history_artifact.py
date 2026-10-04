from __future__ import annotations

import importlib.util
import io
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "restore_history_artifact.py"
SPEC = importlib.util.spec_from_file_location("restore_history_artifact", MODULE_PATH)
restore = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = restore
SPEC.loader.exec_module(restore)


def state_blob(dates=("2026-10-04",)) -> bytes:
    value = {
        "schema_version": 1,
        "window_days": 7,
        "snapshots": {date: {} for date in dates},
    }
    return (json.dumps(value) + "\n").encode("utf-8")


def artifact_zip(blob: bytes, name: str = "history-state.json") -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(name, blob)
    return out.getvalue()


class HistoryArtifactTests(unittest.TestCase):
    def test_select_latest_ignores_expired_artifacts(self):
        payload = {
            "artifacts": [
                {
                    "id": 1,
                    "name": restore.ARTIFACT_NAME,
                    "expired": False,
                    "created_at": "2026-10-03T10:00:00Z",
                    "updated_at": "2026-10-03T10:00:00Z",
                    "archive_download_url": "https://example/1",
                },
                {
                    "id": 2,
                    "name": restore.ARTIFACT_NAME,
                    "expired": True,
                    "created_at": "2026-10-05T10:00:00Z",
                    "updated_at": "2026-10-05T10:00:00Z",
                    "archive_download_url": "https://example/2",
                },
                {
                    "id": 3,
                    "name": restore.ARTIFACT_NAME,
                    "expired": False,
                    "created_at": "2026-10-04T10:00:00Z",
                    "updated_at": "2026-10-04T10:00:00Z",
                    "archive_download_url": "https://example/3",
                },
            ]
        }
        self.assertEqual(restore.select_latest_artifact(payload)["id"], 3)

    def test_extract_history_state_accepts_single_valid_file(self):
        blob = restore.extract_history_state(
            artifact_zip(state_blob(("2026-10-03", "2026-10-04")))
        )
        value = restore.parse_history_state(blob)
        self.assertEqual(
            sorted(value["snapshots"]),
            ["2026-10-03", "2026-10-04"],
        )

    def test_extract_history_state_accepts_nested_artifact_path(self):
        blob = restore.extract_history_state(
            artifact_zip(state_blob(), "state/history-state.json")
        )
        self.assertEqual(restore.parse_history_state(blob)["window_days"], 7)

    def test_extract_history_state_rejects_multiple_state_files(self):
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as zf:
            zf.writestr("a/history-state.json", state_blob())
            zf.writestr("b/history-state.json", state_blob())
        with self.assertRaises(restore.HistoryArtifactError):
            restore.extract_history_state(out.getvalue())

    def test_parse_history_state_rejects_wrong_schema(self):
        blob = json.dumps(
            {"schema_version": 2, "window_days": 7, "snapshots": {}}
        ).encode("utf-8")
        with self.assertRaises(restore.HistoryArtifactError):
            restore.parse_history_state(blob)


if __name__ == "__main__":
    unittest.main()
