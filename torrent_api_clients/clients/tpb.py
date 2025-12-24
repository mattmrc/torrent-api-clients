from __future__ import annotations

from typing import Iterable

import requests

from ..models import TorrentRecord
from ..utils import (
    build_magnet_link,
    build_session,
    extract_resolution,
    extract_year,
    fetch_json,
    format_date_utc,
    format_size_bytes,
)


class TPBClient:
    CAT_HD_MOVIES = 207
    CAT_HD_TV = 208

    def __init__(self, base_url: str, timeout: int, user_agent: str) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = build_session(user_agent)

    def search(self, query: str, category: int, limit: int = 10) -> list[dict]:
        params = {"q": query, "cat": category}
        try:
            data = fetch_json(self.session, self.base_url, params, self.timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"HTTP error while calling API: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("API did not return valid JSON") from exc

        if isinstance(data, dict):
            data = [data]
        if isinstance(data, str):
            return []
        if data and isinstance(data[0], dict) and data[0].get("name") == "No results returned":
            return []

        return data[:limit]

    def search_hd_movies(self, query: str, limit: int = 10) -> list[TorrentRecord]:
        results = self.search(query=query, category=self.CAT_HD_MOVIES, limit=limit)
        return [self._normalize_item(item) for item in results]

    def search_hd_tv(self, query: str, limit: int = 10) -> list[TorrentRecord]:
        results = self.search(query=query, category=self.CAT_HD_TV, limit=limit)
        return [self._normalize_item(item) for item in results]

    def _normalize_item(self, item: dict) -> TorrentRecord:
        name = item.get("name", "")
        size_bytes = item.get("size", "0")
        info_hash = item.get("info_hash", "")
        res_label = extract_resolution(name)[1]

        return TorrentRecord(
            Title=name,
            Year=extract_year(name),
            Resolution=res_label,
            Seeders=str(item.get("seeders", "")),
            Leechers=str(item.get("leechers", "")),
            Size=format_size_bytes(size_bytes),
            UploadedDate=format_date_utc(item.get("added", ""), with_time=False),
            Uploader=str(item.get("username", "")),
            ID=str(item.get("id", "")),
            MagnetLink=build_magnet_link(info_hash, name),
            Source="tpb",
        )

    @staticmethod
    def sort_by_seeders(records: Iterable[TorrentRecord]) -> list[TorrentRecord]:
        def _seeders(item: TorrentRecord) -> int:
            try:
                return int(item.Seeders)
            except (TypeError, ValueError):
                return 0

        return sorted(records, key=_seeders, reverse=True)
