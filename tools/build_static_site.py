#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

SITE_SCHEMA_VERSION = 1
DATA_SCHEMA_VERSION = 1
BUILD_MARKER = ".italy-fuel-pages-build"

PUBLIC_SHELL_FILES = (
    "index.html",
    "static/app.js",
    "static/data-provider.js",
    "static/styles.css",
    "static/vendor/leaflet/LICENSE",
    "static/vendor/leaflet/leaflet.css",
    "static/vendor/leaflet/leaflet.js",
    "static/vendor/leaflet/images/layers-2x.png",
    "static/vendor/leaflet/images/layers.png",
    "static/vendor/leaflet/images/marker-icon-2x.png",
    "static/vendor/leaflet/images/marker-icon.png",
    "static/vendor/leaflet/images/marker-shadow.png",
)

STATIC_RUNTIME_CONFIG = """window.FUEL_MAP_CONFIG=Object.freeze({
 mode:'static',
 dataBase:'./data'
});
"""


class SiteBuildError(RuntimeError):
    pass


def find_repo_root(explicit: str | None = None) -> Path:
    root = (
        Path(explicit).expanduser().resolve()
        if explicit
        else Path(__file__).resolve().parents[1]
    )
    marker = root / "station_map" / "index.html"
    version = root / "station_map" / "fuelmap" / "version.py"
    if not marker.is_file() or not version.is_file():
        raise SiteBuildError(f"Not an italy-fuel-price repository: {root}")
    return root


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SiteBuildError(f"Could not read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SiteBuildError(f"Expected JSON object in {path}")
    return value


def relative_file(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise SiteBuildError(f"Path escapes generated data directory: {relative}") from exc
    if not candidate.is_file():
        raise SiteBuildError(f"Missing generated public data file: {relative}")
    if candidate.is_symlink():
        raise SiteBuildError(f"Generated public data must not contain symlinks: {relative}")
    return candidate


def expected_data_files(data_dir: Path) -> tuple[set[str], dict]:
    metadata_path = relative_file(data_dir, "metadata.json")
    metadata = read_json(metadata_path)
    if metadata.get("schema_version") != DATA_SCHEMA_VERSION:
        raise SiteBuildError(
            f"Unsupported generated-data schema: {metadata.get('schema_version')!r}"
        )

    expected = {"metadata.json"}

    places = metadata.get("places") or {}
    places_path = str(places.get("path") or "places.json")
    relative_file(data_dir, places_path)
    expected.add(places_path)

    localities = metadata.get("localities") or {}
    if localities.get("enabled"):
        locality_path = str(localities.get("path") or "localities.json")
        relative_file(data_dir, locality_path)
        expected.add(locality_path)

    grid = metadata.get("grid") or {}
    cells = grid.get("cells")
    if not isinstance(cells, list) or not cells:
        raise SiteBuildError("Generated metadata has no current-data grid cells")
    for key in cells:
        key = str(key)
        relative = f"cells/{key}.json"
        relative_file(data_dir, relative)
        expected.add(relative)

    history = metadata.get("history") or {}
    if history.get("enabled"):
        history_metadata_path = str(
            history.get("metadata_path") or "history/metadata.json"
        )
        relative_file(data_dir, history_metadata_path)
        expected.add(history_metadata_path)
        history_metadata = read_json(data_dir / history_metadata_path)
        if history_metadata.get("schema_version") != DATA_SCHEMA_VERSION:
            raise SiteBuildError("Unsupported generated-history schema")
        history_cells = history_metadata.get("cells")
        if not isinstance(history_cells, list):
            raise SiteBuildError("Generated history metadata has invalid cells list")
        for key in history_cells:
            relative = f"history/cells/{key}.json"
            relative_file(data_dir, relative)
            expected.add(relative)

    actual = set()
    for path in data_dir.rglob("*"):
        if path.is_symlink():
            raise SiteBuildError(
                "Generated public data must not contain symlinks: "
                f"{path.relative_to(data_dir)}"
            )
        if path.is_file():
            actual.add(path.relative_to(data_dir).as_posix())

    extra = sorted(actual - expected)
    missing = sorted(expected - actual)
    if missing:
        raise SiteBuildError(
            "Generated data is missing declared public files: " + ", ".join(missing)
        )
    if extra:
        raise SiteBuildError(
            "Generated data contains files outside the public allowlist: "
            + ", ".join(extra)
        )
    return expected, metadata


def read_version(repo_root: Path) -> str:
    text = (repo_root / "station_map" / "fuelmap" / "version.py").read_text(
        encoding="utf-8"
    )
    prefix = '__version__ = "'
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(prefix) and line.endswith('"'):
            return line[len(prefix) : -1]
    raise SiteBuildError("Could not read station-map version")


def validate_shell(repo_root: Path, version: str) -> None:
    station_map = repo_root / "station_map"
    for relative in PUBLIC_SHELL_FILES:
        path = station_map / relative
        if not path.is_file():
            raise SiteBuildError(f"Missing public shell asset: station_map/{relative}")
        if path.is_symlink():
            raise SiteBuildError(
                f"Public shell allowlist must not contain symlinks: station_map/{relative}"
            )

    index = (station_map / "index.html").read_text(encoding="utf-8")
    expected_refs = (
        f"./static/styles.css?v={version}",
        f"./static/runtime-config.js?v={version}",
        f"./static/data-provider.js?v={version}",
        f"./static/app.js?v={version}",
    )
    missing = [ref for ref in expected_refs if ref not in index]
    if missing:
        raise SiteBuildError(
            "index.html cache-busting version does not match version.py: "
            + ", ".join(missing)
        )


def prepare_output(output: Path, repo_root: Path, data_dir: Path) -> Path:
    output = output.expanduser().resolve()
    repo_root = repo_root.resolve()
    data_dir = data_dir.resolve()

    protected = {
        Path(output.anchor).resolve(),
        Path.home().resolve(),
        repo_root,
        (repo_root / ".git").resolve(),
        (repo_root / "station_map").resolve(),
        (repo_root / "tools").resolve(),
        (repo_root / "tests").resolve(),
        data_dir,
    }
    protected_trees = (
        (repo_root / ".git").resolve(),
        (repo_root / "station_map").resolve(),
        (repo_root / "tools").resolve(),
        (repo_root / "tests").resolve(),
    )
    overlaps_data = output in data_dir.parents or data_dir in output.parents
    inside_source_tree = any(tree in output.parents for tree in protected_trees)
    if (
        output in protected
        or overlaps_data
        or inside_source_tree
        or (output / ".git").exists()
    ):
        raise SiteBuildError(f"Refusing to replace unsafe output directory: {output}")

    if output.exists():
        entries = list(output.iterdir())
        if entries and not (output / BUILD_MARKER).is_file():
            raise SiteBuildError(
                f"Refusing to replace non-site-builder output directory: {output}"
            )
        if entries:
            shutil.rmtree(output)

    output.mkdir(parents=True, exist_ok=True)
    return output


def copy_public_shell(repo_root: Path, output: Path) -> None:
    station_map = repo_root / "station_map"
    for relative in PUBLIC_SHELL_FILES:
        source = station_map / relative
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    runtime = output / "static" / "runtime-config.js"
    runtime.write_text(STATIC_RUNTIME_CONFIG, encoding="utf-8", newline="\n")


def copy_public_data(data_dir: Path, output: Path, files: set[str]) -> None:
    target = output / "data"
    for relative in sorted(files):
        source = data_dir / relative
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def write_site_files(output: Path, version: str, metadata: dict, data_files: int) -> None:
    (output / ".nojekyll").write_text("", encoding="utf-8")
    manifest = {
        "schema_version": SITE_SCHEMA_VERSION,
        "app_version": version,
        "data_schema_version": metadata.get("schema_version"),
        "data_generated_at": metadata.get("generated_at"),
        "price_date": metadata.get("price_date"),
        "data_files": data_files,
    }
    (output / BUILD_MARKER).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def validate_output(output: Path, expected_data: set[str]) -> None:
    allowed = set(PUBLIC_SHELL_FILES)
    allowed.update(
        {
            "static/runtime-config.js",
            ".nojekyll",
            BUILD_MARKER,
        }
    )
    allowed.update(f"data/{relative}" for relative in expected_data)

    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    extra = sorted(actual - allowed)
    missing = sorted(allowed - actual)
    if extra or missing:
        details = []
        if missing:
            details.append("missing: " + ", ".join(missing))
        if extra:
            details.append("extra: " + ", ".join(extra))
        raise SiteBuildError("Static-site allowlist mismatch; " + "; ".join(details))

    forbidden_suffixes = {
        ".py",
        ".pyc",
        ".sqlite",
        ".sqlite3",
        ".db",
        ".csv",
        ".zip",
        ".env",
    }
    forbidden = [
        relative
        for relative in sorted(actual)
        if Path(relative).suffix.lower() in forbidden_suffixes
    ]
    if forbidden:
        raise SiteBuildError(
            "Forbidden private/source artifact in static site: " + ", ".join(forbidden)
        )


def build_site(repo_root: Path, data_dir: Path, output: Path) -> dict:
    repo_root = repo_root.resolve()
    data_dir = data_dir.expanduser().resolve()
    if not data_dir.is_dir():
        raise SiteBuildError(f"Generated data directory does not exist: {data_dir}")

    version = read_version(repo_root)
    validate_shell(repo_root, version)
    data_files, metadata = expected_data_files(data_dir)
    output = prepare_output(output, repo_root, data_dir)
    copy_public_shell(repo_root, output)
    copy_public_data(data_dir, output, data_files)
    write_site_files(output, version, metadata, len(data_files))
    validate_output(output, data_files)

    total_bytes = sum(
        path.stat().st_size for path in output.rglob("*") if path.is_file()
    )
    return {
        "output": str(output),
        "app_version": version,
        "data_files": len(data_files),
        "site_files": sum(1 for path in output.rglob("*") if path.is_file()),
        "bytes": total_bytes,
        "price_date": metadata.get("price_date"),
    }


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Assemble an allowlisted static site for GitHub Pages."
    )
    ap.add_argument("--repo-root", help="Repository root; normally auto-detected.")
    ap.add_argument(
        "--data-dir",
        required=True,
        help="Validated public data output from tools/build_web_data.py.",
    )
    ap.add_argument(
        "--output",
        required=True,
        help="Static-site directory to create/replace.",
    )
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        repo_root = find_repo_root(args.repo_root)
        result = build_site(
            repo_root,
            Path(args.data_dir),
            Path(args.output),
        )
    except SiteBuildError as exc:
        print(f"error: {exc}")
        return 2

    print(
        "Static site assembled: "
        f"v{result['app_version']}, "
        f"{result['site_files']:,} files, "
        f"{result['bytes'] / 1024 / 1024:.2f} MiB, "
        f"price date {result['price_date'] or 'unknown'}"
    )
    print(result["output"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
