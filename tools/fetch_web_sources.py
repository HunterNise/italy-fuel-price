#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = str(Path(__file__).resolve().parent)
if TOOLS_DIR not in sys.path:
    sys.path.insert(0, TOOLS_DIR)

from istat_localities import (
    ISTAT_LOCALITIES_URL,
    ISTAT_MUNICIPALITIES_2021_URL,
    download_localities,
    download_municipalities_2021,
)

CACHE_MARKER = ".italy-fuel-web-sources.json"
DOWNLOAD_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (5.0, 15.0)


class SourceFetchError(RuntimeError):
    pass


def find_repo_root(explicit: str | None = None) -> Path:
    root = (
        Path(explicit).expanduser().resolve()
        if explicit
        else Path(__file__).resolve().parents[1]
    )
    marker = root / "station_map" / "fuelmap" / "mimit.py"
    if not marker.is_file():
        raise SourceFetchError(f"Not an italy-fuel-price repository: {root}")
    return root


def import_mimit(repo_root: Path):
    station_map = str(repo_root / "station_map")
    if station_map not in sys.path:
        sys.path.insert(0, station_map)
    from fuelmap import mimit
    from fuelmap.config import PRICE_URL, STATION_URL

    return mimit, PRICE_URL, STATION_URL


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def download_with_retry(
    label: str,
    download_fn,
    *,
    attempts: int = DOWNLOAD_ATTEMPTS,
    delays: tuple[float, ...] = RETRY_DELAYS_SECONDS,
    sleep_fn=time.sleep,
) -> bytes:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    for attempt in range(1, attempts + 1):
        try:
            return download_fn()
        except OSError as exc:
            if attempt >= attempts:
                raise SourceFetchError(
                    f"{label} download failed after {attempts} attempts: {exc}"
                ) from exc
            delay = delays[min(attempt - 1, len(delays) - 1)] if delays else 0
            print(
                f"{label} download failed (attempt {attempt}/{attempts}): "
                f"{exc}; retrying in {delay:g}s",
                file=sys.stderr,
            )
            sleep_fn(delay)

    raise AssertionError("unreachable")


def prepare_output(path: Path, repo_root: Path) -> Path:
    path = path.expanduser().resolve()
    repo_root = repo_root.resolve()
    protected = {
        Path(path.anchor).resolve(),
        Path.home().resolve(),
        repo_root,
        (repo_root / ".git").resolve(),
        (repo_root / "station_map").resolve(),
        (repo_root / "tools").resolve(),
        (repo_root / "tests").resolve(),
    }
    protected_trees = (
        (repo_root / ".git").resolve(),
        (repo_root / "station_map").resolve(),
        (repo_root / "tools").resolve(),
        (repo_root / "tests").resolve(),
    )
    if path in protected or any(tree in path.parents for tree in protected_trees):
        raise SourceFetchError(f"Refusing unsafe source-cache directory: {path}")

    if path.exists():
        entries = list(path.iterdir())
        if entries and not (path / CACHE_MARKER).is_file():
            raise SourceFetchError(
                f"Refusing to replace non-source-cache directory: {path}"
            )
        if entries:
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_bundle(
    output: Path,
    *,
    registry_blob: bytes,
    price_blob: bytes,
    locality_blob: bytes,
    municipality_blob: bytes,
    source_urls: dict[str, str],
) -> dict:
    files = {
        "anagrafica_impianti_attivi.csv": registry_blob,
        "prezzo_alle_8.csv": price_blob,
        "LocalitaPuntuali_21.zip": locality_blob,
        "Limiti2021_g.zip": municipality_blob,
    }
    for name, blob in files.items():
        (output / name).write_bytes(blob)

    manifest = {
        "schema_version": 1,
        "downloaded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "files": {
            name: {
                "bytes": len(blob),
                "sha256": sha256(blob),
                "source_url": source_urls[name],
            }
            for name, blob in files.items()
        },
    }
    (output / CACHE_MARKER).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def fetch(repo_root: Path, output: Path) -> dict:
    mimit, price_url, station_url = import_mimit(repo_root)

    # Download every upstream object before touching the output directory so a
    # failed request cannot leave a half-new snapshot bundle behind.
    registry_blob = download_with_retry(
        "MIMIT registry", lambda: mimit.download(station_url)
    )
    price_blob = download_with_retry(
        "MIMIT prices", lambda: mimit.download(price_url)
    )
    locality_blob = download_with_retry(
        "ISTAT localities", download_localities
    )
    municipality_blob = download_with_retry(
        "ISTAT municipalities", download_municipalities_2021
    )

    output = prepare_output(output, repo_root)
    return write_bundle(
        output,
        registry_blob=registry_blob,
        price_blob=price_blob,
        locality_blob=locality_blob,
        municipality_blob=municipality_blob,
        source_urls={
            "anagrafica_impianti_attivi.csv": station_url,
            "prezzo_alle_8.csv": price_url,
            "LocalitaPuntuali_21.zip": ISTAT_LOCALITIES_URL,
            "Limiti2021_g.zip": ISTAT_MUNICIPALITIES_2021_URL,
        },
    )


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description=(
            "Download one coherent source bundle for static build + parity checks."
        )
    )
    ap.add_argument("--repo-root", help="Repository root; normally auto-detected.")
    ap.add_argument("--output", required=True, help="Source-cache directory.")
    return ap


def main() -> int:
    args = parser().parse_args()
    try:
        repo_root = find_repo_root(args.repo_root)
        manifest = fetch(repo_root, Path(args.output))
    except (SourceFetchError, OSError) as exc:
        print(f"fetch_web_sources: {exc}", file=sys.stderr)
        return 2

    print(
        "Downloaded web sources: "
        + ", ".join(
            f"{name} ({meta['bytes'] / 1024 / 1024:.2f} MiB)"
            for name, meta in manifest["files"].items()
        )
    )
    print(Path(args.output).expanduser().resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
