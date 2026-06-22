#!/usr/bin/env python3
"""Shared Canvas API helpers for the POSC/CRJU 320 Summer Session B 2026 build scripts."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

SOURCE_COURSE_ID = "3548509"  # Summer 2025 CRJU 320-53 (10-week offering)
TARGET_COURSE_ID = "3579296"  # Summer 2026 CRJU/POSC 320-50 (5-week Session B)

IDS_FILE = Path(__file__).parent / "ids.json"

PACIFIC = ZoneInfo("America/Los_Angeles")

# Monday-of-week and Friday-of-week dates for Summer Session B 2026 (Jun 29 - Jul 31).
WEEK_DATES: dict[int, dict[str, datetime]] = {
    week: {
        "unlock_at": datetime.combine(monday, time(0, 0), tzinfo=PACIFIC),
        "due_at": datetime.combine(friday, time(23, 59), tzinfo=PACIFIC),
        "lock_at": datetime.combine(friday, time(23, 59), tzinfo=PACIFIC),
    }
    for week, (monday, friday) in {
        1: (datetime(2026, 6, 29).date(), datetime(2026, 7, 3).date()),
        2: (datetime(2026, 7, 6).date(), datetime(2026, 7, 10).date()),
        3: (datetime(2026, 7, 13).date(), datetime(2026, 7, 17).date()),
        4: (datetime(2026, 7, 20).date(), datetime(2026, 7, 24).date()),
        5: (datetime(2026, 7, 27).date(), datetime(2026, 7, 31).date()),
    }.items()
}


def iso(dt: datetime) -> str:
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def canvas_request(
    method: str,
    path: str,
    params: list[tuple[str, str]] | None = None,
    course_id: str = TARGET_COURSE_ID,
) -> Any:
    base_url = env("CANVAS_BASE_URL")
    token = env("CANVAS_TOKEN")

    url = f"{base_url.rstrip('/')}/{path.lstrip('/').format(course_id=course_id)}"
    data = None
    headers = {"Authorization": f"Bearer {token}"}
    if method == "GET" and params:
        parsed = urllib.parse.urlsplit(url)
        query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query.extend(params)
        url = urllib.parse.urlunsplit(parsed._replace(query=urllib.parse.urlencode(query)))
    elif params:
        data = urllib.parse.urlencode(params).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason} for {method} {url}: {body}") from e
    return json.loads(body) if body else None


def canvas_get_all(path: str, course_id: str, params: list[tuple[str, str]] | None = None) -> list[Any]:
    """GET a paginated Canvas list endpoint, following Link headers via per_page=100."""
    all_params = list(params or [])
    if not any(k == "per_page" for k, _ in all_params):
        all_params.append(("per_page", "100"))
    result = canvas_request("GET", path, all_params, course_id=course_id)
    return result if isinstance(result, list) else [result]


def load_ids() -> dict[str, Any]:
    if IDS_FILE.exists():
        return json.loads(IDS_FILE.read_text())
    return {}


def save_ids(data: dict[str, Any]) -> None:
    IDS_FILE.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def merge_ids(section: str, values: dict[str, Any]) -> None:
    data = load_ids()
    data.setdefault(section, {}).update(values)
    save_ids(data)


@dataclass(frozen=True)
class Criterion:
    description: str
    points: float
    long_description: str


@dataclass(frozen=True)
class RubricSpec:
    assignment_id: int
    assignment_name: str
    title: str
    criteria: tuple[Criterion, ...]


def upload_course_file(course_id: str, local_path: Path, content_type: str) -> dict[str, Any]:
    """Upload a local file to a course's Files via the Canvas 3-step upload flow."""
    file_bytes = local_path.read_bytes()

    step1 = canvas_request(
        "POST",
        "/api/v1/courses/{course_id}/files",
        [
            ("name", local_path.name),
            ("size", str(len(file_bytes))),
            ("content_type", content_type),
            ("parent_folder_path", "build-uploads"),
            ("on_duplicate", "overwrite"),
        ],
        course_id=course_id,
    )

    upload_url = step1["upload_url"]
    upload_params = step1["upload_params"]

    boundary = "----canvas-build-script-boundary----"
    parts: list[bytes] = []
    for key, value in upload_params.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    parts.append(f"--{boundary}\r\n".encode())
    parts.append(
        f'Content-Disposition: form-data; name="file"; filename="{local_path.name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n".encode()
    )
    parts.append(file_bytes)
    parts.append(f"\r\n--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        upload_url,
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            response_body = resp.read().decode("utf-8")
            final_url = resp.url
    except urllib.error.HTTPError as e:
        response_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {e.reason} uploading {local_path.name}: {response_body}") from e

    if response_body.strip():
        result = json.loads(response_body)
    else:
        # Some Canvas instances redirect to a confirmation endpoint instead of
        # returning the file JSON directly.
        confirm_req = urllib.request.Request(
            final_url, headers={"Authorization": f"Bearer {env('CANVAS_TOKEN')}"}
        )
        with urllib.request.urlopen(confirm_req, timeout=30) as confirm_resp:
            result = json.loads(confirm_resp.read().decode("utf-8"))

    return result
