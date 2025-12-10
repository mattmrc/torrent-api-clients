import csv
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests


class TPBClient:
    BASE_URL = "https://apibay.org/q.php"

    # Commonly used TPB category IDs
    CAT_HD_MOVIES = 207   # HD - Movies
    CAT_HD_TV = 208       # HD - TV shows

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    # ------------- Low-level HTTP + JSON -------------

    def _search(self, query: str, category: int, limit: int = 10) -> list[dict]:
        """
        Call the apibay/thepiratebay JSON API and return raw result dicts.
        """
        params = {
            "q": query,
            "cat": category,
        }

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(f"HTTP error while calling API: {exc}") from exc

        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError("API did not return valid JSON") from exc

        # Normalize into a list
        if isinstance(data, dict):
            data = [data]
        if isinstance(data, str):
            # Some implementations use a string like "No results returned"
            return []

        # Sometimes the API may return a single "No results returned" entry
        if data and isinstance(data[0], dict) and data[0].get("name") == "No results returned":
            return []

        return data[:limit]

    # ------------- Public search methods -------------

    def search_hd_movies(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search HD movies.
        """
        return self._search(query=query, category=self.CAT_HD_MOVIES, limit=limit)

    def search_hd_tv(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search HD TV shows.
        """
        return self._search(query=query, category=self.CAT_HD_TV, limit=limit)

    # ------------- Helper / formatting methods -------------

    @staticmethod
    def _human_size(size_bytes_str: str) -> str:
        """
        Convert size from bytes (string) to human-readable (e.g. '1.23 GB').
        """
        try:
            size = int(size_bytes_str)
        except (TypeError, ValueError):
            return "unknown"

        units = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size >= 1024 and i < len(units) - 1:
            size /= 1024.0
            i += 1
        return f"{size:.2f} {units[i]}"

    @staticmethod
    def _format_timestamp(ts_str: str) -> str:
        """
        Convert Unix timestamp (string) to 'YYYY-MM-DD' (UTC).
        """
        try:
            ts = int(ts_str)
            dt = datetime.fromtimestamp(ts, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d")
        except (TypeError, ValueError, OSError):
            return "unknown"

    @staticmethod
    def _extract_year(name: str) -> str:
        """
        Best-effort extraction of a year from the torrent name.
        Looks for a 4-digit number between 1900 and 2099.
        """
        if not name:
            return ""

        candidates = re.findall(r"(19\d{2}|20\d{2})", name)
        if not candidates:
            return ""

        # Often the last one is the most relevant (e.g. 'Movie.2019.1080p')
        return candidates[-1]

    @staticmethod
    def _extract_resolution(name: str) -> str:
        """
        Best-effort extraction of resolution from the torrent name.
        """
        if not name:
            return ""

        lower = name.lower()

        # Check more specific / common patterns first
        for res in ["2160p", "2160", "4k", "1440p", "1080p", "720p", "480p"]:
            if res in lower:
                if res in ["2160", "4k"]:
                    return "2160p"
                return res

        return ""

    @staticmethod
    def _seeders_as_int(item: dict) -> int:
        """
        Safely convert the 'seeders' field of a raw item to int for sorting.
        """
        try:
            return int(item.get("seeders", 0))
        except (TypeError, ValueError):
            return 0

    # ------------- Transformation + CSV export -------------

    def _transform_item(self, item: dict) -> dict:
        """
        Transform raw API item into a normalized dict for CSV output.
        Column names are already capitalized for direct CSV writing.
        """
        name = item.get("name", "")
        size_bytes = item.get("size", "0")
        info_hash = item.get("info_hash", "")

        magnet = ""
        if info_hash:
            # Simple magnet link with hash and encoded display name
            magnet = f"magnet:?xt=urn:btih:{info_hash}"
            if name:
                magnet += f"&dn={quote(name)}"

        return {
            "Title": name,
            "Year": self._extract_year(name),
            "Resolution": self._extract_resolution(name),
            "Seeders": item.get("seeders", ""),
            "Leechers": item.get("leechers", ""),
            "Size": self._human_size(size_bytes),
            "UploadedDate": self._format_timestamp(item.get("added", "")),
            "Uploader": item.get("username", ""),
            "ID": item.get("id", ""),
            "MagnetLink": magnet,
        }

    def save_results_to_csv(self, items: list[dict], output_path: str | Path) -> None:
        """
        Transform raw results and save them as a CSV file, sorted by seeders (desc).

        The CSV column names are capitalized and include:
        Title, Year, Resolution, Seeders, Leechers, Size, UploadedDate, Uploader, ID, Magnet
        """
        if not items:
            print("No items to save.")
            return

        # Ensure we always sort by seeders descending regardless of API behavior
        sorted_items = sorted(items, key=self._seeders_as_int, reverse=True)
        transformed = [self._transform_item(item) for item in sorted_items]

        fieldnames = [
            "Title",
            "Year",
            "Resolution",
            "Seeders",
            "Leechers",
            "Size",
            "UploadedDate",
            "Uploader",
            "ID",
            "MagnetLink",
        ]

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(transformed)

        print(f"Saved {len(transformed)} rows to {path.resolve()}")


# ------------- CLI entrypoint tying everything together -------------


def main() -> int:
    client = TPBClient()

    print("Choose search type:")
    print("  1) HD Movies")
    print("  2) HD TV Shows")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        search_kind = "movie"
        subfolder = "Movies"
        search_func = client.search_hd_movies
    elif choice == "2":
        search_kind = "TV show"
        subfolder = "TV_Shows"
        search_func = client.search_hd_tv
    else:
        print("Invalid choice, exiting.")
        return 1

    query = input(f"Search {search_kind}s for: ").strip()
    if not query:
        print("Empty query, exiting.")
        return 0

    try:
        results = search_func(query=query, limit=50)
    except RuntimeError as exc:
        print(f"Error while searching: {exc}")
        return 1

    if not results:
        print("No results found.")
        return 0

    # Build base directory and filename:
    # Outputs/Movies/{query}.csv or Outputs/TV_Shows/{query}.csv
    safe_query = re.sub(r"[^\w\-]+", "_", query).strip("_")
    base_dir = Path("Outputs") / subfolder
    output_path = base_dir / f"{safe_query}.csv"

    client.save_results_to_csv(results, output_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
