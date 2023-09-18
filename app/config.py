import enum
import shutil
import sys
from pathlib import Path
from typing import Dict, Optional

import yaml
from pydantic import BaseSettings, root_validator, validator

settings = None

class ExecutionMode(enum.Enum):
    DEV = "dev"
    REGISTRY = "registry"
    CLIENT = "client"
    EXPLORER = "explorer"

class ServerPort(enum.Enum):
    DEV = 31999
    CLIMATE_WAREHOUSE = 31310
    CLIMATE_PORTAL = 31311
    CLIMATE_TOKEN_REGISTRY = 31312
    CLIMATE_EXPLORER = 31313
    CLIMATE_TOKEN_CLIENT = 31314


class Settings(BaseSettings):
    _instance = None
    _HIDDEN_FIELDS = ["MODE", "CHIA_ROOT", "CONFIG_PATH", "SERVER_PORT"]

    # Hidden configs: not exposed in config.yaml
    MODE: ExecutionMode
    CHIA_ROOT: Path = Path("~/.chia/mainnet")
    CONFIG_PATH: Path = Path("climate_token/config/config.yaml")
    SERVER_PORT: Optional[int]

    # Visible configs: configurable through config.yaml
    LOG_PATH: Path = Path("climate_token/log/debug.log")
    DB_PATH: Path = Path("climate_explorer/db/climate_activity_CHALLENGE.sqlite")

    SERVER_HOST: str = "0.0.0.0"
    BLOCK_START: int = 1_500_000
    BLOCK_RANGE: int = 10_000
    MIN_DEPTH: int = 4
    # we always look back ~36 hours since the climate warehouse waits 24 hours before
    # setting metadata to be readable
    LOOKBACK_DEPTH: int = 6_912
    # fee is in mojos
    DEFAULT_FEE: int = 1_000_000_000
    CADT_API_SERVER_HOST: str = "https://api.climatewarehouse.chia.net"
    CADT_API_KEY: Optional[str] = None
    CHIA_HOSTNAME: str = "localhost"
    CHIA_FULL_NODE_RPC_PORT: int = 8555
    CHIA_WALLET_RPC_PORT: int = 9256
    CLIMATE_EXPLORER_PORT: Optional[int] = None
    CLIMATE_TOKEN_CLIENT_PORT: Optional[int] = None
    CLIMATE_TOKEN_REGISTRY_PORT: Optional[int] = None
    DEV_PORT: Optional[int] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = get_settings()
        return cls._instance

    @root_validator
    def configure_port(cls, values):
        settings = cls.get_instance()

        if settings is None:
            print("Settings is None.")
            return values
        
        print(f"MODE: {values['MODE']}, Settings: {settings.__dict__}")

        if values["MODE"] == ExecutionMode.REGISTRY:
            values["SERVER_PORT"] = int(getattr(settings, 'CLIMATE_TOKEN_REGISTRY_PORT', ServerPort.CLIMATE_TOKEN_REGISTRY.value))
        elif values["MODE"] == ExecutionMode.CLIENT:
            values["SERVER_PORT"] = int(getattr(settings, 'CLIMATE_TOKEN_CLIENT_PORT', ServerPort.CLIMATE_TOKEN_CLIENT.value))
        elif values["MODE"] == ExecutionMode.EXPLORER:
            values["SERVER_PORT"] = int(getattr(settings, 'CLIMATE_EXPLORER_PORT', ServerPort.CLIMATE_EXPLORER.value))
        elif values["MODE"] == ExecutionMode.DEV:
            values["SERVER_PORT"] = int(getattr(settings, 'DEV_PORT', ServerPort.DEV.value))
        else:
            raise ValueError(f"Invalid mode {values['MODE']}!")
        
        print(f"Set SERVER_PORT to {values['SERVER_PORT']}")
        return values

    @validator("CHIA_ROOT", pre=True)
    def expand_root(cls, v):
        return Path(v).expanduser()

    @validator("CONFIG_PATH", "LOG_PATH", "DB_PATH")
    def prepend_root(cls, v, values):
        v: Path = values["CHIA_ROOT"] / v
        parent: Path = v.parent
        parent.mkdir(parents=True, exist_ok=True)
        return v


def get_settings() -> Settings:
    if Settings._instance is None: 
        in_pyinstaller: bool = getattr(sys, "frozen", False)

        default_env_file: Path
        default_config_file: Path
        if in_pyinstaller:
            default_env_file = Path(sys._MEIPASS) / ".env"
            default_config_file = Path(sys._MEIPASS) / "config.yaml"
        else:
            default_env_file = Path(".env")
            default_config_file = Path("config.yaml")

        default_settings = Settings(_env_file=default_env_file)
        config_file: Path = default_settings.CONFIG_PATH

        settings: Settings
        settings_dict: Dict
        if not config_file.is_file():
            config_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(default_config_file, config_file)

        with open(config_file, "r") as f:
            settings_dict = yaml.safe_load(f)

        settings_dict = default_settings.dict() | (settings_dict or {})
        settings = Settings(**settings_dict)
        Settings._instance = Settings(**settings_dict)

    return Settings._instance


settings = get_settings()
