import csv
from datetime import datetime, timezone
from pathlib import Path

import requests


class EZTVClient:
    """Client to interact with the EZTV API, filter results, and save to CSV."""

    def __init__(self, base_url: str = "https://eztvx.to/api/get-torrents"):
        self.base_url = base_url

        # Outputs/TV_Shows under the script directory
        self.script_directory = Path(__file__).resolve().parent
        self.output_folder = self.script_directory / "Outputs" / "TV_Shows"
        self.output_folder.mkdir(parents=True, exist_ok=True)

    # --- Utility methods (static) ---

    @staticmethod
    def format_file_size(size_in_bytes: str) -> str:
        """Convert bytes to human-readable format (KB, MB, GB, TB)."""
        try:
            value = float(size_in_bytes)
        except (ValueError, TypeError):
            return "Unknown"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if value < 1024.0:
                return f"{value:.2f} {unit}"
            value /= 1024.0

        return f"{value:.2f} PB"

    @staticmethod
    def format_date(unix_timestamp: str) -> str:
        """Convert Unix timestamp to a readable UTC date string."""
        try:
            ts = int(unix_timestamp)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError, OSError):
            return "Unknown Date"

    @staticmethod
    def get_resolution(title: str) -> tuple:
        """Return (rank, label) resolution tuple inferred from title.

        Rank 4: 2160p / 4K / UHD
        Rank 3: 1080p
        Rank 2: 720p
        Rank 1: SD / Unknown
        """
        title_lower = title.lower()

        if "2160p" in title_lower or "4k" in title_lower or "uhd" in title_lower:
            return 4, "2160p (4K)"
        if "1080p" in title_lower:
            return 3, "1080p"
        if "720p" in title_lower:
            return 2, "720p"
        return 1, "SD / Unknown"

    @staticmethod
    def is_high_quality(title: str) -> bool:
        """Return True if the title indicates 1080p or higher."""
        rank, _ = EZTVClient.get_resolution(title)
        return rank >= 3

    # --- Internal helpers ---

    def _fetch_data(self, params: dict) -> list[dict]:
        """Perform the HTTP request and return a list of torrent dicts."""
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
        except requests.RequestException as exc:
            print(f"[Error] Connection failed: {exc}")
            return []

        if response.status_code != 200:
            print(f"[Error] API returned status code: {response.status_code}")
            return []

        try:
            data = response.json()
        except ValueError as exc:
            print(f"[Error] Response was not valid JSON: {exc}")
            return []

        torrents = data.get("torrents")
        if not torrents:
            print("[Info] No torrents found in response.")
            return []

        return torrents

    def _sort_key_generator(self, item: dict) -> tuple:
        """Sort key: (season, episode, -resolution_rank, -seeds)."""
        # Season / Episode numeric
        try:
            s_num = int(item.get("season", 0))
        except (ValueError, TypeError):
            s_num = 0

        try:
            e_num = int(item.get("episode", 0))
        except (ValueError, TypeError):
            e_num = 0

        # Resolution rank
        res_rank, _ = self.get_resolution(item.get("title", ""))

        # Seeds
        try:
            seeds = int(item.get("seeds", 0))
        except (ValueError, TypeError):
            seeds = 0

        # Negatives for descending on rank & seeds
        return s_num, e_num, -res_rank, -seeds

    def _save_to_csv(self, data_list: list[dict], filename_prefix: str) -> None:
        """Write a list of torrents to CSV in Outputs/TV_Shows."""
        if not data_list:
            print(f"--> No data to save for '{filename_prefix}'.")
            return

        current_time = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{filename_prefix}_{current_time}.csv"
        full_path = self.output_folder / filename

        header = [
            "Title",
            "Season",
            "Episode",
            "Resolution",
            "Size",
            "Seeds",
            "Peers",
            "ReleaseDate",
            "MagnetLink",
        ]

        try:
            with full_path.open(mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(header)

                count = 0
                for item in data_list:
                    title = item.get("title", "Unknown Title")
                    season = item.get("season", "N/A")
                    episode = item.get("episode", "N/A")

                    _, res_label = self.get_resolution(title)
                    size = self.format_file_size(item.get("size_bytes", 0))
                    seeds = item.get("seeds", 0)
                    peers = item.get("peers", 0)
                    release_date = self.format_date(item.get("date_released_unix", 0))
                    magnet = item.get("magnet_url", "N/A")

                    row = [
                        title,
                        season,
                        episode,
                        res_label,
                        size,
                        seeds,
                        peers,
                        release_date,
                        magnet,
                    ]
                    writer.writerow(row)
                    count += 1

            print(f"Success! Saved {count} items to: {full_path}")
        except Exception as exc:
            print(f"Error saving CSV: {exc}")

    # --- Public methods ---

    def get_latest(self, limit: int = 50, page: int = 1, min_1080p: bool = False) -> None:
        """Fetch latest torrents and save them."""
        print(f"--> Fetching latest {limit} items (Page {page})...")

        params = {"limit": limit, "page": page}
        results = self._fetch_data(params)

        if min_1080p:
            print("--> Filtering for 1080p+ quality...")
            results = [item for item in results if self.is_high_quality(item.get("title", ""))]

        self._save_to_csv(results, "latest_torrents")

    def get_show_by_imdb(
        self,
        imdb_id: str,
        show_name: str = "Show",
        season: int | None = None,
        min_1080p: bool = False,
    ) -> None:
        """Fetch torrents for a specific IMDB ID and save, sorted by S/E/resolution/seeds."""
        safe_name = show_name.replace(" ", "_")
        print(f"--> Searching for '{show_name}' (IMDB: {imdb_id})...")

        params = {"limit": 100, "imdb_id": imdb_id, "page": 1}
        results = self._fetch_data(params)

        # Filter by season
        if season is not None:
            results = [item for item in results if str(item.get("season")) == str(season)]
            prefix = f"{safe_name}_S{int(season):02d}"
        else:
            prefix = f"{safe_name}_All"

        # Filter by quality
        if min_1080p:
            results = [item for item in results if self.is_high_quality(item.get("title", ""))]
            prefix += "_HQ"

        # Sort using the multi-level key
        results.sort(key=self._sort_key_generator)
        self._save_to_csv(results, prefix)

    def get_top_seeded(
        self,
        limit_fetch: int = 100,
        top_n: int = 20,
        min_1080p: bool = False,
    ) -> None:
        """Fetch a batch, optionally filter by quality, and save the top-N by seeds."""
        print(f"--> Analyzing top seeded items (Scanning {limit_fetch} items)...")

        params = {"limit": limit_fetch, "page": 1}
        results = self._fetch_data(params)

        if min_1080p:
            results = [item for item in results if self.is_high_quality(item.get("title", ""))]

        # Sort by seeds descending
        results.sort(
            key=lambda x: int(x.get("seeds", 0)) if isinstance(x.get("seeds", 0), (int, str)) else 0,
            reverse=True,
        )

        top_results = results[:top_n]
        self._save_to_csv(top_results, f"top_{top_n}_seeded")


def main() -> int:
    client = EZTVClient()

    # Example usage: The Good Wife, IMDB ID 1442462, Season 1
    client.get_show_by_imdb(
        imdb_id="1442462",
        show_name="The Good Wife",
        season=1,
        min_1080p=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())