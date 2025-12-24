from __future__ import annotations

import argparse
from pathlib import Path

from .config import AppConfig
from .clients.eztv import EZTVClient
from .clients.tpb import TPBClient
from .utils import resolve_output_path, safe_filename, write_csv


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="torrent-api-clients",
        description="Query torrent metadata APIs and export normalized CSVs.",
    )
    parser.add_argument("--config", type=Path, help="Path to a config TOML file")
    parser.add_argument("--output", type=Path, help="Override output directory")
    parser.add_argument("--append", action="store_true", help="Append rows to an existing CSV")
    parser.add_argument("--no-timestamp", action="store_true", help="Do not add timestamp to filenames")

    subparsers = parser.add_subparsers(dest="provider", required=True)

    tpb_parser = subparsers.add_parser("tpb", help="The Pirate Bay client")
    tpb_sub = tpb_parser.add_subparsers(dest="command", required=True)

    tpb_search = tpb_sub.add_parser("search", help="Search TPB for HD movies or TV")
    tpb_search.add_argument("--query", required=True, help="Search query")
    tpb_search.add_argument(
        "--category",
        choices=["movies", "tv"],
        default="movies",
        help="TPB category (HD movies or TV)",
    )
    tpb_search.add_argument("--limit", type=int, default=50, help="Max results to fetch")

    eztv_parser = subparsers.add_parser("eztv", help="EZTV client")
    eztv_sub = eztv_parser.add_subparsers(dest="command", required=True)

    latest = eztv_sub.add_parser("latest", help="Fetch latest EZTV torrents")
    latest.add_argument("--limit", type=int, default=50, help="Max results to fetch")
    latest.add_argument("--page", type=int, default=1, help="Page number")
    latest.add_argument("--min-1080p", action="store_true", help="Filter for 1080p+")

    show = eztv_sub.add_parser("show", help="Fetch torrents for a show by IMDb ID")
    show.add_argument("--imdb-id", required=True, help="IMDb ID (numbers only)")
    show.add_argument("--show-name", default="Show", help="Used for output filename")
    show.add_argument("--season", type=int, help="Season number")
    show.add_argument("--min-1080p", action="store_true", help="Filter for 1080p+")

    top = eztv_sub.add_parser("top", help="Fetch top-seeded EZTV torrents")
    top.add_argument("--limit-fetch", type=int, default=100, help="Batch size to scan")
    top.add_argument("--top-n", type=int, default=20, help="How many top items to save")
    top.add_argument("--min-1080p", action="store_true", help="Filter for 1080p+")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config = AppConfig.load(args.config)
    output_dir = args.output or config.output_dir
    timestamp = not args.no_timestamp

    if args.provider == "tpb":
        client = TPBClient(
            base_url=config.tpb_base_url,
            timeout=config.timeout,
            user_agent=config.user_agent,
        )
        query = args.query
        safe_query = safe_filename(query)
        category_label = "movies" if args.category == "movies" else "tv"
        prefix = f"tpb_{category_label}_{safe_query}"

        if args.category == "movies":
            records = client.search_hd_movies(query=query, limit=args.limit)
        else:
            records = client.search_hd_tv(query=query, limit=args.limit)

        records = TPBClient.sort_by_seeders(records)
        output_path = resolve_output_path(output_dir, prefix, args.append, timestamp)
        count = write_csv(records, output_path, append=args.append)
        print(f"Saved {count} rows to {output_path.resolve()}")
        return 0

    if args.provider == "eztv":
        client = EZTVClient(
            base_url=config.eztv_base_url,
            timeout=config.timeout,
            user_agent=config.user_agent,
        )

        if args.command == "latest":
            records = client.get_latest(
                limit=args.limit,
                page=args.page,
                min_1080p=args.min_1080p or config.min_1080p,
            )
            prefix = "eztv_latest"
            output_path = resolve_output_path(output_dir, prefix, args.append, timestamp)
            count = write_csv(records, output_path, append=args.append)
            print(f"Saved {count} rows to {output_path.resolve()}")
            return 0

        if args.command == "show":
            records = client.get_show_by_imdb(
                imdb_id=args.imdb_id,
                season=args.season,
                min_1080p=args.min_1080p or config.min_1080p,
            )
            prefix = f"eztv_{safe_filename(args.show_name)}"
            if args.season is not None:
                prefix += f"_S{int(args.season):02d}"
            output_path = resolve_output_path(output_dir, prefix, args.append, timestamp)
            records = EZTVClient.sort_by_episode(records)
            count = write_csv(records, output_path, append=args.append)
            print(f"Saved {count} rows to {output_path.resolve()}")
            return 0

        if args.command == "top":
            records = client.get_top_seeded(
                limit_fetch=args.limit_fetch,
                top_n=args.top_n,
                min_1080p=args.min_1080p or config.min_1080p,
            )
            prefix = f"eztv_top_{args.top_n}_seeded"
            output_path = resolve_output_path(output_dir, prefix, args.append, timestamp)
            count = write_csv(records, output_path, append=args.append)
            print(f"Saved {count} rows to {output_path.resolve()}")
            return 0

    parser.print_help()
    return 1
