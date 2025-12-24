from __future__ import annotations

from torrent_api_clients.clients.eztv import EZTVClient
from torrent_api_clients.config import AppConfig
from torrent_api_clients.utils import resolve_output_path, safe_filename, write_csv


def main() -> int:
    config = AppConfig.load()
    client = EZTVClient(
        base_url=config.eztv_base_url,
        timeout=config.timeout,
        user_agent=config.user_agent,
    )

    # Example usage: The Good Wife, IMDB ID 1442462, Season 1
    records = client.get_show_by_imdb(
        imdb_id="1442462",
        season=1,
        min_1080p=config.min_1080p,
    )
    records = EZTVClient.sort_by_episode(records)

    prefix = f"eztv_{safe_filename('The Good Wife')}_S01"
    output_path = resolve_output_path(config.output_dir, prefix, append=False, timestamp=True)
    count = write_csv(records, output_path, append=False)

    print(f"Saved {count} rows to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
