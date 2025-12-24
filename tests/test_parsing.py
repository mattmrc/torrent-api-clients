from torrent_api_clients.utils import (
    extract_resolution,
    extract_year,
    format_date_utc,
    format_size_bytes,
)


def test_extract_year():
    assert extract_year("Movie.2019.1080p") == "2019"
    assert extract_year("Classic.1995.Remaster") == "1995"
    assert extract_year("No.Year.Here") == ""


def test_extract_resolution():
    assert extract_resolution("Show.S01E01.2160p")[1] == "2160p"
    assert extract_resolution("Show.1080p")[1] == "1080p"
    assert extract_resolution("Show.720p")[1] == "720p"
    assert extract_resolution("Show")[1] == ""


def test_format_size_bytes():
    assert format_size_bytes(1024) == "1.00 KB"
    assert format_size_bytes("1048576") == "1.00 MB"


def test_format_date_utc():
    assert format_date_utc(0) == "1970-01-01"
    assert format_date_utc(0, with_time=True) == "1970-01-01 00:00:00"
