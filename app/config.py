import enum
import sys
from pathlib import Path
from typing import Dict

import yaml
from pydantic import BaseSettings, validator


class ExecutionMode(enum.Enum):
    DEV = "dev"
    REGISTRY = "registry"
    CLIENT = "client"
    EXPLORER = "explorer"


class Settings(BaseSettings):
    _HIDDEN_FIELDS = ["MODE", "CHIA_ROOT", "CONFIG_PATH"]

    # Hidden configs: not exposed in config.yaml
    MODE: ExecutionMode
    CHIA_ROOT: Path = Path("~/.chia/mainnet")
    CONFIG_PATH: Path = Path("climate_token/config/config.yaml")

    # Visiable configs: configurable through config.yaml
    LOG_PATH: Path = Path("climate_token/log/debug.log")
    DB_PATH: Path = Path("climate_explorer/db/climate_activity_{CHALLENGE}.sqlite")

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 31313
    BLOCK_START: int = 1500000
    BLOCK_RANGE: int = 10000
    MIN_DEPTH: int = 4
    CLIMATE_API_URL: str = "https://api.climatewarehouse.chia.net"
    CHIA_HOSTNAME: str = "localhost"
    CHIA_FULL_NODE_RPC_PORT: int = 8555
    CHIA_WALLET_RPC_PORT: int = 9256

    @validator("CHIA_ROOT", pre=True)
    def expand_root(cls, v):
        return Path(v).expanduser()

    @validator("CONFIG_PATH", "LOG_PATH", "DB_PATH")
    def prepend_root(cls, v, values):
        v: Path = values["CHIA_ROOT"] / v
        parent: Path = v.parent
        if not parent.is_dir():
            parent.mkdir(parents=True)
        return v


def get_settings() -> Settings:
    in_pyinstaller: bool = getattr(sys, "frozen", False)

    default_env_file: Path
    if in_pyinstaller:
        default_env_file = Path(sys._MEIPASS / ".env")
    else:
        default_env_file = Path(".env")

    default_settings = Settings(_env_file=default_env_file)
    config_file: Path = default_settings.CONFIG_PATH

    settings: Settings
    settings_dict: Dict
    if config_file.is_file():
        with open(config_file, "r") as f:
            settings_dict = yaml.safe_load(f)

        settings_dict = default_settings.dict() | settings_dict
        settings = Settings(**settings_dict)

    else:
        config_file.parent.mkdir(parents=True)

        settings_dict = default_settings.dict()
        for field in Settings._HIDDEN_FIELDS:
            del settings_dict[field]

        with open(config_file, "w") as f:
            yaml.safe_dump(settings_dict, f)

        settings = default_settings

    return settings


settings = get_settings()
