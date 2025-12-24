from __future__ import annotations

import csv
import os
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .models import CSV_HEADERS, TorrentRecord


def build_session(user_agent: str, retries: int = 3, backoff: float = 0.5) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        backoff_factor=backoff,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": user_agent})
    return session


def fetch_json(session: requests.Session, url: str, params: dict, timeout: int) -> dict | list:
    response = session.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def format_size_bytes(size_in_bytes: str | int | float) -> str:
    try:
        value = float(size_in_bytes)
    except (TypeError, ValueError):
        return "Unknown"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if value < 1024.0:
            return f"{value:.2f} {unit}"
        value /= 1024.0

    return f"{value:.2f} PB"


def format_date_utc(timestamp: str | int | float, with_time: bool = False) -> str:
    try:
        ts = int(timestamp)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return "Unknown Date"

    if with_time:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d")


def extract_year(title: str) -> str:
    if not title:
        return ""

    candidates = re.findall(r"(19\d{2}|20\d{2})", title)
    if not candidates:
        return ""

    return candidates[-1]


def extract_resolution(title: str) -> tuple[int, str]:
    if not title:
        return 1, ""

    lower = title.lower()
    if "2160p" in lower or "4k" in lower or "uhd" in lower:
        return 4, "2160p"
    if "1440p" in lower:
        return 3, "1440p"
    if "1080p" in lower:
        return 3, "1080p"
    if "720p" in lower:
        return 2, "720p"
    if "480p" in lower:
        return 2, "480p"
    return 1, ""


def is_high_quality(title: str) -> bool:
    rank, _ = extract_resolution(title)
    return rank >= 3


def build_magnet_link(info_hash: str, name: str) -> str:
    if not info_hash:
        return ""

    magnet = f"magnet:?xt=urn:btih:{info_hash}"
    if name:
        magnet += f"&dn={quote(name)}"
    return magnet


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^\w\-]+", "_", value).strip("_")
    return cleaned or "results"


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def resolve_output_path(
    output_dir: Path,
    filename_prefix: str,
    append: bool,
    timestamp: bool = True,
) -> Path:
    if append or not timestamp:
        return output_dir / f"{filename_prefix}.csv"

    current_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
    return output_dir / f"{filename_prefix}_{current_time}.csv"


def write_csv(records: Iterable[TorrentRecord], output_path: Path, append: bool = False) -> int:
    ensure_output_dir(output_path.parent)

    mode = "a" if append else "w"
    file_exists = output_path.exists()
    count = 0

    with output_path.open(mode, newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_HEADERS)
        if not append or not file_exists:
            writer.writeheader()

        for record in records:
            row = asdict(record)
            writer.writerow(row)
            count += 1

    return count


def apply_env_override(config: dict, key: str, env_var: str, parser) -> None:
    raw = os.getenv(env_var)
    if raw is None:
        return
    config[key] = parser(raw)
