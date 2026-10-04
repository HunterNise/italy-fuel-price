from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_static_site.py"
SPEC = importlib.util.spec_from_file_location("build_static_site", MODULE_PATH)
site = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = site
SPEC.loader.exec_module(site)


def make_repo(root: Path, version: str = "0.9.3") -> Path:
    station = root / "station_map"
    (station / "fuelmap").mkdir(parents=True)
    (station / "fuelmap" / "version.py").write_text(
        f'__version__ = "{version}"\n', encoding="utf-8"
    )
    (station / "index.html").write_text(
        "\n".join(
            [
                f'<link rel="stylesheet" href="./static/styles.css?v={version}"/>',
                f'<script src="./static/runtime-config.js?v={version}"></script>',
                f'<script src="./static/data-provider.js?v={version}"></script>',
                f'<script src="./static/app.js?v={version}"></script>',
            ]
        ),
        encoding="utf-8",
    )
    for relative in site.PUBLIC_SHELL_FILES:
        if relative == "index.html":
            continue
        path = station / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"public\n")
    return root


def make_data(root: Path, *, localities: bool = True, history: bool = True) -> Path:
    data = root / "generated-data"
    (data / "cells").mkdir(parents=True)
    (data / "cells" / "87_22.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "cell": "87_22",
                "stations": [],
            }
        ),
        encoding="utf-8",
    )
    (data / "places.json").write_text(
        json.dumps({"schema_version": 1, "places": []}),
        encoding="utf-8",
    )

    metadata = {
        "schema_version": 1,
        "generated_at": "2026-10-04T20:00:00+00:00",
        "price_date": "2026-10-04",
        "grid": {"cells": ["87_22"]},
        "places": {"path": "places.json"},
        "localities": {"enabled": localities, "path": "localities.json"},
        "history": {
            "enabled": history,
            "metadata_path": "history/metadata.json",
        },
    }
    if localities:
        (data / "localities.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "fields": ["name", "type", "pro_com", "municipality", "lat", "lon"],
                    "localities": [],
                }
            ),
            encoding="utf-8",
        )
    if history:
        (data / "history" / "cells").mkdir(parents=True)
        (data / "history" / "metadata.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "cells": ["87_22"],
                    "days": ["2026-10-04"],
                }
            ),
            encoding="utf-8",
        )
        (data / "history" / "cells" / "87_22.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "cell": "87_22",
                    "stations": {},
                }
            ),
            encoding="utf-8",
        )

    (data / "metadata.json").write_text(
        json.dumps(metadata),
        encoding="utf-8",
    )
    return data


class StaticSiteTests(unittest.TestCase):
    def test_build_copies_only_public_allowlist_and_generates_static_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)
            output = root / "site"

            result = site.build_site(repo, data, output)

            self.assertEqual(result["app_version"], "0.9.3")
            self.assertTrue((output / ".nojekyll").is_file())
            self.assertTrue((output / site.BUILD_MARKER).is_file())
            self.assertIn(
                "mode:'static'",
                (output / "static" / "runtime-config.js").read_text(encoding="utf-8"),
            )
            self.assertFalse((output / "station_map").exists())
            self.assertFalse(any(output.rglob("*.py")))
            self.assertFalse(any(output.rglob("*.sqlite")))
            self.assertTrue((output / "data" / "metadata.json").is_file())
            self.assertTrue((output / "data" / "localities.json").is_file())
            self.assertTrue(
                (output / "data" / "history" / "cells" / "87_22.json").is_file()
            )

    def test_generated_data_with_unexpected_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)
            (data / "station_history.sqlite").write_bytes(b"private")
            with self.assertRaises(site.SiteBuildError):
                site.build_site(repo, data, root / "site")

    def test_missing_declared_cell_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)
            (data / "cells" / "87_22.json").unlink()
            with self.assertRaises(site.SiteBuildError):
                site.build_site(repo, data, root / "site")

    def test_non_builder_output_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)
            output = root / "site"
            output.mkdir()
            (output / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(site.SiteBuildError):
                site.build_site(repo, data, output)
            self.assertTrue((output / "keep.txt").is_file())

    def test_previous_builder_output_can_be_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)
            output = root / "site"
            site.build_site(repo, data, output)
            (output / "obsolete.txt").write_text("old", encoding="utf-8")
            site.build_site(repo, data, output)
            self.assertFalse((output / "obsolete.txt").exists())


    def test_repo_root_site_directory_is_allowed_but_source_tree_is_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo")
            data = make_data(root)

            site.build_site(repo, data, repo / "_site")
            self.assertTrue((repo / "_site" / "index.html").is_file())

            with self.assertRaises(site.SiteBuildError):
                site.build_site(repo, data, repo / "station_map" / "_site")

    def test_index_version_must_match_version_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = make_repo(root / "repo", version="0.9.3")
            data = make_data(root)
            index = repo / "station_map" / "index.html"
            index.write_text(
                index.read_text(encoding="utf-8").replace(
                    "styles.css?v=0.9.3", "styles.css?v=0.9.2"
                ),
                encoding="utf-8",
            )
            with self.assertRaises(site.SiteBuildError):
                site.build_site(repo, data, root / "site")


if __name__ == "__main__":
    unittest.main()
