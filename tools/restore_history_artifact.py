#!/usr/bin/env python3
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

API_ROOT = "https://api.github.com"
API_VERSION = "2026-03-10"
ARTIFACT_NAME = "pages-history-state"
HISTORY_SCHEMA_VERSION = 1


class HistoryArtifactError(RuntimeError):
    pass


def _headers(token: str) -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VERSION,
        "User-Agent": "italy-fuel-price history-state restore/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def api_json(url: str, token: str) -> dict:
    request = urllib.request.Request(url, headers=_headers(token))
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            value = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HistoryArtifactError(f"GitHub artifact API request failed: {exc}") from exc
    if not isinstance(value, dict):
        raise HistoryArtifactError("GitHub artifact API returned a non-object response")
    return value


def select_latest_artifact(payload: dict) -> dict | None:
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        raise HistoryArtifactError("GitHub artifact list has no `artifacts` array")

    candidates = [
        item
        for item in artifacts
        if isinstance(item, dict)
        and item.get("name") == ARTIFACT_NAME
        and not item.get("expired")
        and item.get("archive_download_url")
    ]
    if not candidates:
        return None

    candidates.sort(
        key=lambda item: (
            str(item.get("created_at") or ""),
            str(item.get("updated_at") or ""),
            int(item.get("id") or 0),
        ),
        reverse=True,
    )
    return candidates[0]


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def download_artifact_zip(artifact: dict, token: str) -> bytes:
    url = str(artifact.get("archive_download_url") or "")
    if not url:
        raise HistoryArtifactError("Artifact has no archive_download_url")

    request = urllib.request.Request(url, headers=_headers(token))
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        response = opener.open(request, timeout=60)
    except urllib.error.HTTPError as exc:
        if exc.code not in (301, 302, 303, 307, 308):
            raise HistoryArtifactError(
                f"Artifact download request failed with HTTP {exc.code}"
            ) from exc
        location = exc.headers.get("Location")
    else:
        try:
            location = response.headers.get("Location")
            if not location:
                return response.read()
        finally:
            response.close()

    if not location:
        raise HistoryArtifactError("GitHub artifact download did not return a redirect")

    try:
        with urllib.request.urlopen(location, timeout=120) as response:
            return response.read()
    except OSError as exc:
        raise HistoryArtifactError(f"Artifact object download failed: {exc}") from exc


def parse_history_state(blob: bytes) -> dict:
    try:
        value = json.loads(blob.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HistoryArtifactError("Restored history state is not valid JSON") from exc
    if not isinstance(value, dict):
        raise HistoryArtifactError("Restored history state must be a JSON object")
    if value.get("schema_version") != HISTORY_SCHEMA_VERSION:
        raise HistoryArtifactError(
            f"Unsupported history-state schema: {value.get('schema_version')!r}"
        )
    if not isinstance(value.get("snapshots"), dict):
        raise HistoryArtifactError("Restored history state has invalid snapshots")
    if int(value.get("window_days") or 0) != 7:
        raise HistoryArtifactError("Restored history state must use a seven-day window")
    return value


def extract_history_state(archive_blob: bytes) -> bytes:
    try:
        zf = zipfile.ZipFile(io.BytesIO(archive_blob))
    except zipfile.BadZipFile as exc:
        raise HistoryArtifactError("Downloaded Actions artifact is not a ZIP") from exc

    matches = [
        name
        for name in zf.namelist()
        if not name.endswith("/") and Path(name).name == "history-state.json"
    ]
    if len(matches) != 1:
        raise HistoryArtifactError(
            "Expected exactly one history-state.json in artifact; "
            f"found {matches}"
        )

    blob = zf.read(matches[0])
    parse_history_state(blob)
    return blob


def restore(
    repository: str,
    output: Path,
    token: str,
    *,
    allow_missing: bool = False,
) -> dict:
    if "/" not in repository:
        raise HistoryArtifactError(
            "Repository must be in owner/name form, for example OWNER/REPO"
        )

    query = urllib.parse.urlencode(
        {
            "name": ARTIFACT_NAME,
            "per_page": 100,
        }
    )
    payload = api_json(
        f"{API_ROOT}/repos/{repository}/actions/artifacts?{query}",
        token,
    )
    artifact = select_latest_artifact(payload)
    if artifact is None:
        if allow_missing:
            return {"restored": False}
        raise HistoryArtifactError(f"No non-expired `{ARTIFACT_NAME}` artifact found")

    archive_blob = download_artifact_zip(artifact, token)
    state_blob = extract_history_state(archive_blob)

    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(state_blob)

    workflow_run = artifact.get("workflow_run") or {}
    state = parse_history_state(state_blob)
    dates = sorted(state["snapshots"])
    return {
        "restored": True,
        "artifact_id": artifact.get("id"),
        "created_at": artifact.get("created_at"),
        "head_branch": workflow_run.get("head_branch"),
        "head_sha": workflow_run.get("head_sha"),
        "snapshot_dates": dates,
    }


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Restore the newest rolling Pages history state from Actions artifacts."
    )
    ap.add_argument(
        "--repository",
        default=os.environ.get("GITHUB_REPOSITORY"),
        help="GitHub repository in owner/name form; defaults to GITHUB_REPOSITORY.",
    )
    ap.add_argument("--output", required=True, help="Path to restored history-state JSON.")
    ap.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN", ""),
        help="GitHub token; defaults to GITHUB_TOKEN.",
    )
    ap.add_argument(
        "--allow-missing",
        action="store_true",
        help="Exit successfully when no previous state artifact exists.",
    )
    return ap


def main() -> int:
    args = parser().parse_args()
    if not args.repository:
        print("restore_history_artifact: repository is required", file=sys.stderr)
        return 2

    try:
        result = restore(
            args.repository,
            Path(args.output),
            args.token,
            allow_missing=args.allow_missing,
        )
    except HistoryArtifactError as exc:
        print(f"restore_history_artifact: {exc}", file=sys.stderr)
        return 2

    if not result["restored"]:
        print("No previous Pages history-state artifact found; starting fresh.")
        return 0

    dates = result["snapshot_dates"]
    print(
        "Restored Pages history state from artifact "
        f"{result['artifact_id']} ({result['created_at']}, "
        f"branch {result['head_branch'] or 'unknown'}): "
        f"{', '.join(dates) if dates else 'no snapshots'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
