# Torrent API Clients: TPB & EZTV

Small Python tools to explore two public torrent-related APIs (for **learning and academic purposes** only):

* A **The Pirate Bay (TPB)** client using the unofficial JSON backend (`apibay`-style API)
* An **EZTV** client using the official EZTV JSON API

Both scripts focus on **metadata only** (titles, seeders, resolution, etc.) and save results to CSV files for analysis.

> ⚠️ **Important:** These scripts are for educational use only. Do not use them to download or share copyrighted content. See the Legal & Ethics section below.

---

## Features

### Common

* Written in **Python 3.11+**
* Simple **CLI entrypoint** (`python tpb_client.py`, `python eztv_client.py`)
* Uses only the `requests` library from PyPI
* Exports results to CSV into a consistent folder structure:

  * `Outputs/Movies/…`
  * `Outputs/TV_Shows/…`
* CSV columns are **normalized and capitalized** for easier downstream use (e.g., in pandas)

---

### TPB Client (`tpb_client.py`)

Client for the The Pirate Bay JSON backend (`apibay`-style API).

**Key capabilities:**

* `TPBClient.search_hd_movies(query, limit=10)`

  * Searches **HD Movies** (TPB category `207`)
* `TPBClient.search_hd_tv(query, limit=10)`

  * Searches **HD TV Shows** (TPB category `208`)
* Converts:

  * size in bytes → human-readable `Size` (e.g., `1.23 GB`)
  * Unix timestamp → `UploadedDate` (`YYYY-MM-DD`)
* Heuristics to extract:

  * `Year` from the title (e.g. `"Movie.2019.1080p"` → `2019`)
  * `Resolution` from the title (`2160p`, `1080p`, `720p`, etc.)
* Creates **magnet links** from the `info_hash` + title
* Sorts results by **Seeders (descending)** before saving

**CSV output (Movies & TV):**

Saved to:

* Movies: `Outputs/Movies/<query>.csv`
* TV: `Outputs/TV_Shows/<query>.csv`

Columns:

* `Title`
* `Year`
* `Resolution`
* `Seeders`
* `Leechers`
* `Size`
* `UploadedDate`
* `Uploader`
* `ID`
* `MagnetLink`

---

### EZTV Client (`eztv_client.py`)

Client for the EZTV API (`https://eztvx.to/api/get-torrents` style endpoint).

This script is **TV-specific** and always writes into `Outputs/TV_Shows`.

**Key capabilities:**

* `get_latest(limit=50, page=1, min_1080p=False)`

  * Fetches the latest torrents from EZTV
  * Optional filter for **1080p or higher**
* `get_show_by_imdb(imdb_id, show_name="Show", season=None, min_1080p=False)`

  * Fetches torrents for a specific TV show using its **IMDb ID**
  * Optional:

    * `season` filter
    * 1080p+ quality filter
  * Results are sorted by:

    1. Season
    2. Episode
    3. Resolution (higher first)
    4. Seeds (descending)
* `get_top_seeded(limit_fetch=100, top_n=20, min_1080p=False)`

  * Fetches a batch and saves the top **N** most seeded torrents

**CSV output (TV only):**

Saved to:

* `Outputs/TV_Shows/<prefix>_<timestamp>.csv`

Columns:

* `Title`
* `Season`
* `Episode`
* `Resolution`
* `Size`
* `Seeds`
* `Peers`
* `ReleaseDate`
* `MagnetLink`

---

## Requirements

* **Python**: 3.11 or newer recommended
* **Dependencies** (install via pip):

```bash
pip install requests
```

---

## Repository Structure

Suggested structure if you publish this as-is:

```text
.
├── tpb_client.py
├── eztv_client.py
├── Outputs/
│   ├── Movies/
│   └── TV_Shows/
└── README.md
```

The `Outputs` folder and its subfolders are created automatically at runtime if they don’t exist yet.

---

## Usage

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Install dependencies

```bash
pip install requests
```

(Optionally use a virtual environment.)

---

### TPB client

**Run:**

```bash
python tpb_client.py
```

You’ll be prompted to:

1. Choose search type:

   * `1` → HD Movies
   * `2` → HD TV Shows
2. Enter a search query (e.g. `Inception`, `The Good Wife`)

The script will:

* Call the TPB JSON API
* Sort results **by Seeders (descending)**
* Normalize fields
* Save a CSV to:

  * `Outputs/Movies/<query>.csv` for movies
  * `Outputs/TV_Shows/<query>.csv` for TV shows

You can also import the class and call it directly from another script or a notebook:

```python
from tpb_client import TPBClient

client = TPBClient()
results = client.search_hd_tv("The Good Wife", limit=50)
```

---

### EZTV client

**Run:**

```bash
python eztv_client.py
```

The default `main()` can be adjusted to whatever use case you want (e.g., fetch a specific show/season). Example in code:

```python
if __name__ == "__main__":
    client = EZTVClient()
    client.get_show_by_imdb(
        imdb_id="1442462",         # The Good Wife
        show_name="The Good Wife",
        season=1,
        min_1080p=False,
    )
```

This will:

* Fetch torrents for “The Good Wife” Season 1
* Sort results by Season, Episode, Resolution (2160p/1080p/720p/SD) and Seeds
* Save a CSV to `Outputs/TV_Shows/The_Good_Wife_S01_YYYY-MM-DD_HH-MM-SS.csv`

You can change the calls in `main()` to use:

* `get_latest(...)`
* `get_top_seeded(...)`
* or different IMDb IDs / seasons

---

## Customization Ideas

Some easy extensions if you want to evolve this project:

* Load the generated CSVs into **pandas** for:

  * distribution of resolutions
  * popularity over time
  * correlation between size and seeders
* Add **CLI arguments** with `argparse` instead of interactive input
* Add a small **config file** (YAML/JSON) to define:

  * default output directories
  * default limits / filters
* Wrap both clients in a **simple API** (e.g., FastAPI app) so you can query them locally via HTTP

---

## Legal & Ethics

These scripts:

* Only fetch and process **metadata** (titles, sizes, seeders, etc.).
* Are intended for **learning**, **API exploration**, and **data engineering practice**.

However:

* Many torrents on TPB and EZTV point to copyrighted content.
* Downloading or sharing copyrighted material without permission may be illegal in your jurisdiction.
* ISPs in some countries may block these sites or their APIs.

**You are solely responsible** for how you use this code.
Only use it with content you are legally allowed to access.

---

## License

MIT License
Copyright (c) 2025 Matheus Cabral

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


---

## Disclaimer

This project is **not affiliated with** or endorsed by The Pirate Bay, EZTV, or any other website or entity.
APIs and endpoints used here are unofficial and may change or stop working at any time.
