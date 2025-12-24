from __future__ import annotations

from typing import Iterable

import requests

from ..models import TorrentRecord
from ..utils import (
    build_session,
    extract_resolution,
    fetch_json,
    format_date_utc,
    format_size_bytes,
    is_high_quality,
)


class EZTVClient:
    def __init__(self, base_url: str, timeout: int, user_agent: str) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = build_session(user_agent)

    def _fetch(self, params: dict) -> list[dict]:
        try:
            data = fetch_json(self.session, self.base_url, params, self.timeout)
        except requests.RequestException as exc:
            raise RuntimeError(f"HTTP error while calling API: {exc}") from exc
        except ValueError as exc:
            raise RuntimeError("API did not return valid JSON") from exc

        torrents = data.get("torrents") if isinstance(data, dict) else None
        if not torrents:
            return []

        return torrents

    def get_latest(
        self,
        limit: int = 50,
        page: int = 1,
        min_1080p: bool = False,
    ) -> list[TorrentRecord]:
        params = {"limit": limit, "page": page}
        results = self._fetch(params)
        if min_1080p:
            results = [item for item in results if is_high_quality(item.get("title", ""))]
        return [self._normalize_item(item) for item in results]

    def get_show_by_imdb(
        self,
        imdb_id: str,
        season: int | None = None,
        min_1080p: bool = False,
    ) -> list[TorrentRecord]:
        params = {"limit": 100, "imdb_id": imdb_id, "page": 1}
        results = self._fetch(params)
        if season is not None:
            results = [item for item in results if str(item.get("season")) == str(season)]
        if min_1080p:
            results = [item for item in results if is_high_quality(item.get("title", ""))]
        return [self._normalize_item(item) for item in results]

    def get_top_seeded(
        self,
        limit_fetch: int = 100,
        top_n: int = 20,
        min_1080p: bool = False,
    ) -> list[TorrentRecord]:
        params = {"limit": limit_fetch, "page": 1}
        results = self._fetch(params)
        if min_1080p:
            results = [item for item in results if is_high_quality(item.get("title", ""))]

        results.sort(key=self._seeders_sort, reverse=True)
        return [self._normalize_item(item) for item in results[:top_n]]

    @staticmethod
    def _seeders_sort(item: dict) -> int:
        try:
            return int(item.get("seeds", 0))
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def sort_by_episode(records: Iterable[TorrentRecord]) -> list[TorrentRecord]:
        def _key(item: TorrentRecord) -> tuple:
            try:
                s_num = int(item.Season)
            except (TypeError, ValueError):
                s_num = 0
            try:
                e_num = int(item.Episode)
            except (TypeError, ValueError):
                e_num = 0
            res_rank, _ = extract_resolution(item.Title)
            try:
                seeds = int(item.Seeders)
            except (TypeError, ValueError):
                seeds = 0
            return (s_num, e_num, -res_rank, -seeds)

        return sorted(records, key=_key)

    def _normalize_item(self, item: dict) -> TorrentRecord:
        title = item.get("title", "")
        res_label = extract_resolution(title)[1]

        return TorrentRecord(
            Title=title,
            Resolution=res_label,
            Seeders=str(item.get("seeds", "")),
            Peers=str(item.get("peers", "")),
            Size=format_size_bytes(item.get("size_bytes", 0)),
            ReleaseDate=format_date_utc(item.get("date_released_unix", ""), with_time=True),
            MagnetLink=str(item.get("magnet_url", "")),
            Season=str(item.get("season", "")),
            Episode=str(item.get("episode", "")),
            Source="eztv",
        )
