from __future__ import annotations

from torrent_api_clients.clients.tpb import TPBClient
from torrent_api_clients.config import AppConfig
from torrent_api_clients.utils import resolve_output_path, safe_filename, write_csv


def main() -> int:
    config = AppConfig.load()
    client = TPBClient(
        base_url=config.tpb_base_url,
        timeout=config.timeout,
        user_agent=config.user_agent,
    )

    print("Choose search type:")
    print("  1) HD Movies")
    print("  2) HD TV Shows")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        search_kind = "movie"
        category = "movies"
        search_func = client.search_hd_movies
    elif choice == "2":
        search_kind = "TV show"
        category = "tv"
        search_func = client.search_hd_tv
    else:
        print("Invalid choice, exiting.")
        return 1

    query = input(f"Search {search_kind}s for: ").strip()
    if not query:
        print("Empty query, exiting.")
        return 0

    try:
        records = search_func(query=query, limit=50)
    except RuntimeError as exc:
        print(f"Error while searching: {exc}")
        return 1

    if not records:
        print("No results found.")
        return 0

    records = TPBClient.sort_by_seeders(records)
    safe_query = safe_filename(query)
    prefix = f"tpb_{category}_{safe_query}"
    output_path = resolve_output_path(config.output_dir, prefix, append=False, timestamp=True)
    count = write_csv(records, output_path, append=False)

    print(f"Saved {count} rows to {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
