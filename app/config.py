import enum
import os
import sys
from pathlib import Path

from pydantic import BaseSettings

IN_PYINSTALLER = getattr(sys, "frozen", False)


class ExecutionMode(enum.Enum):
    DEV = "dev"
    REGISTRY = "registry"
    CLIENT = "client"
    EXPLORER = "explorer"


class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 31313
    BLOCK_START: int = 1500000
    BLOCK_RANGE: int = 10000
    MIN_DEPTH: int = 32
    CLIMATE_API_URL: str = "https://api.climatewarehouse.chia.net"
    CHIA_ROOT: Path = Path.home() / ".chia" / "mainnet"
    CHIA_HOSTNAME: str = "localhost"
    CHIA_FULL_NODE_RPC_PORT: int = 8555
    CHIA_WALLET_RPC_PORT: int = 9256
    MODE: ExecutionMode

    class Config:
        env_file = os.path.join(sys._MEIPASS, ".env") if IN_PYINSTALLER else ".env"
