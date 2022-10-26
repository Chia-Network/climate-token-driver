import enum
import sys
from pathlib import Path

import yaml
from pydantic import BaseSettings, validator


class ExecutionMode(enum.Enum):
    DEV = "dev"
    REGISTRY = "registry"
    CLIENT = "client"
    EXPLORER = "explorer"


class Settings(BaseSettings):
    CHIA_ROOT: Path = Path("~/.chia/mainnet")
    MODE: ExecutionMode

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 31313
    BLOCK_START: int = 1500000
    BLOCK_RANGE: int = 10000
    MIN_DEPTH: int = 32
    CLIMATE_API_URL: str = "https://api.climatewarehouse.chia.net"
    CHIA_HOSTNAME: str = "localhost"
    CHIA_FULL_NODE_RPC_PORT: int = 8555
    CHIA_WALLET_RPC_PORT: int = 9256

    @validator("CHIA_ROOT")
    def convert_path(cls, v):
        return Path(v).expanduser()


def get_settings() -> Settings:
    in_pyinstaller: bool = getattr(sys, "frozen", False)

    default_env_file: Path
    if in_pyinstaller:
        default_env_file = Path(sys._MEIPASS / ".env")
    else:
        default_env_file = Path(".env")

    default_settings = Settings(_env_file=default_env_file)

    root_path: Path = default_settings.CHIA_ROOT / "climate_token"
    config_dir: Path = root_path / "config"
    config_file: Path = config_dir / "config.yaml"

    settings: Settings
    settings_dict: Dict
    if config_file.is_file():
        with open(config_file, "r") as f:
            settings_dict = yaml.safe_load(f)

        settings_dict = default_settings.dict() | settings_dict
        settings = Settings(**settings_dict)

    else:
        config_dir.mkdir(parents=True)

        settings_dict = default_settings.dict()
        del settings_dict["CHIA_ROOT"]
        del settings_dict["MODE"]

        with open(config_file, "w") as f:
            yaml.safe_dump(settings_dict, f)

        settings = default_settings

    return settings


settings = get_settings()
