# Torrent API Clients: TPB & EZTV

Small Python tools to explore two public torrent-related APIs (for **learning and academic purposes** only). They only fetch **metadata** (titles, seeders, resolution, etc.) and export normalized CSVs.

> ⚠️ **Important:** Do not use this code to download or share copyrighted content. See Legal & Ethics below.

---

## Features

- Python 3.11+ package with a unified CLI (`torrent-api-clients`)
- Shared normalization for both APIs with consistent CSV columns
- Config file + environment variable overrides
- Output hygiene: safe filenames, timestamps, and append mode
- Resilient HTTP with retries, timeouts, and a custom User-Agent

---

## Quick start

Conda (recommended if you use Conda):

```bash
conda env create -f environment.yml
conda activate torrent-api-clients

# TPB: HD movies
python -m torrent_api_clients tpb search --query "Inception" --category movies

# EZTV: latest torrents
python -m torrent_api_clients eztv latest --limit 50
```

Pip:

```bash
pip install -r requirements.txt
python -m torrent_api_clients tpb search --query "The Good Wife" --category tv
```

---

## CLI usage

### TPB

```bash
python -m torrent_api_clients tpb search \
  --query "Inception" \
  --category movies \
  --limit 50
```

### EZTV

Latest torrents:

```bash
python -m torrent_api_clients eztv latest --limit 50 --page 1
```

Show by IMDb ID:

```bash
python -m torrent_api_clients eztv show \
  --imdb-id 1442462 \
  --show-name "The Good Wife" \
  --season 1
```

Top seeded:

```bash
python -m torrent_api_clients eztv top --limit-fetch 100 --top-n 20
```

### Common flags

- `--output`: override output directory
- `--append`: append to an existing CSV
- `--no-timestamp`: keep filenames stable (no timestamp)

---

## CSV output

All CSVs share a consistent schema:

```
Title,Year,Resolution,Seeders,Leechers,Size,UploadedDate,Uploader,ID,MagnetLink,Season,Episode,Peers,ReleaseDate,Source
```

Output filenames follow a consistent prefix + timestamp pattern, for example:

- `Outputs/tpb_movies_Inception_2025-01-10_12-00-00.csv`
- `Outputs/eztv_latest_2025-01-10_12-00-00.csv`

---

## Configuration

You can configure defaults via TOML or environment variables.

### Config file

Create one of these:

- `./torrent_api_clients.toml`
- `~/.config/torrent_api_clients/config.toml`

Example:

```toml
output_dir = "Outputs"
timeout = 10
tpb_base_url = "https://apibay.org/q.php"
eztv_base_url = "https://eztvx.to/api/get-torrents"
user_agent = "torrent-api-clients/0.1"
min_1080p = false
```

### Environment overrides

- `TAC_OUTPUT_DIR`
- `TAC_TIMEOUT`
- `TAC_TPB_BASE_URL`
- `TAC_EZTV_BASE_URL`
- `TAC_USER_AGENT`
- `TAC_MIN_1080P`

---

## Repository structure

```text
.
├── torrent_api_clients/
│   ├── clients/
│   ├── cli.py
│   ├── config.py
│   ├── models.py
│   └── utils.py
├── tests/
├── legacy/
│   ├── tpb_client.py
│   └── eztv_client.py
└── readme.md
```

Legacy scripts (`legacy/tpb_client.py`, `legacy/eztv_client.py`) still work and now use the shared library.

---

## Development

Conda:

```bash
conda env create -f environment.yml
conda activate torrent-api-clients
```

Pip:

```bash
pip install -e ".[dev]"
```

Then run:

```bash
python -m ruff check .
python -m ruff format --check .
python -m mypy torrent_api_clients
python -m pytest
```

---

## Legal & Ethics

These scripts:

- Only fetch and process **metadata** (titles, sizes, seeders, etc.).
- Are intended for **learning**, **API exploration**, and **data engineering practice**.

However:

- Many torrents on TPB and EZTV point to copyrighted content.
- Downloading or sharing copyrighted material without permission may be illegal.
- ISPs in some countries may block these sites or their APIs.

**You are solely responsible** for how you use this code. Only use it with content you are legally allowed to access.

---

## License

MIT License. See `LICENSE`.

---

## Disclaimer

This project is **not affiliated with** or endorsed by The Pirate Bay, EZTV, or any other website or entity. APIs and endpoints used here are unofficial and may change or stop working at any time.
