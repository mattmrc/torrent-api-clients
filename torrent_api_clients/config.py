from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from .utils import apply_env_override


DEFAULT_USER_AGENT = "torrent-api-clients/0.1 (+https://example.invalid)"


@dataclass
class AppConfig:
    output_dir: Path
    timeout: int
    tpb_base_url: str
    eztv_base_url: str
    user_agent: str
    min_1080p: bool

    @classmethod
    def load(cls, config_path: Path | None = None) -> "AppConfig":
        data: dict[str, Any] = {}
        if config_path:
            data.update(_load_toml(config_path))
        else:
            data.update(_load_toml(_global_config_path()))
            data.update(_load_toml(_local_config_path()))

        defaults = {
            "output_dir": "Outputs",
            "timeout": 10,
            "tpb_base_url": "https://apibay.org/q.php",
            "eztv_base_url": "https://eztvx.to/api/get-torrents",
            "user_agent": DEFAULT_USER_AGENT,
            "min_1080p": False,
        }
        merged = {**defaults, **data}

        apply_env_override(merged, "output_dir", "TAC_OUTPUT_DIR", str)
        apply_env_override(merged, "timeout", "TAC_TIMEOUT", int)
        apply_env_override(merged, "tpb_base_url", "TAC_TPB_BASE_URL", str)
        apply_env_override(merged, "eztv_base_url", "TAC_EZTV_BASE_URL", str)
        apply_env_override(merged, "user_agent", "TAC_USER_AGENT", str)
        apply_env_override(merged, "min_1080p", "TAC_MIN_1080P", _parse_bool)

        return cls(
            output_dir=Path(merged["output_dir"]).expanduser(),
            timeout=int(merged["timeout"]),
            tpb_base_url=str(merged["tpb_base_url"]),
            eztv_base_url=str(merged["eztv_base_url"]),
            user_agent=str(merged["user_agent"]),
            min_1080p=bool(merged["min_1080p"]),
        )


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _global_config_path() -> Path:
    return Path.home() / ".config" / "torrent_api_clients" / "config.toml"


def _local_config_path() -> Path:
    return Path.cwd() / "torrent_api_clients.toml"


def _load_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    if tomllib is None:
        raise RuntimeError("tomllib is required on Python 3.11+ to load config files")
    with path.open("rb") as handle:
        return tomllib.load(handle)
