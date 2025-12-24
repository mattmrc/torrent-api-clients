from __future__ import annotations

from dataclasses import dataclass

CSV_HEADERS = [
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
    "Season",
    "Episode",
    "Peers",
    "ReleaseDate",
    "Source",
]


@dataclass
class TorrentRecord:
    Title: str = ""
    Year: str = ""
    Resolution: str = ""
    Seeders: str = ""
    Leechers: str = ""
    Size: str = ""
    UploadedDate: str = ""
    Uploader: str = ""
    ID: str = ""
    MagnetLink: str = ""
    Season: str = ""
    Episode: str = ""
    Peers: str = ""
    ReleaseDate: str = ""
    Source: str = ""
