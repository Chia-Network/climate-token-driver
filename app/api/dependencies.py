from __future__ import annotations

import enum
import logging
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from pathlib import Path

from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.rpc_client import RpcClient
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import get_session_local_cls

logger = logging.getLogger("ClimateToken")


def get_db_session_context() -> AbstractAsyncContextManager[Session]:
    return asynccontextmanager(get_db_session)()


async def get_db_session() -> Session:
    SessionLocal = await get_session_local_cls()

    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class NodeType(str, enum.Enum):
    FULL_NODE = "FULL_NODE"
    WALLET = "WALLET"


async def _get_rpc_client(
    node_type: NodeType,
    self_hostname: str,
    rpc_port: int,
    root_path: Path = DEFAULT_ROOT_PATH,
) -> AsyncGenerator[RpcClient, None]:
    rpc_client_cls = {
        NodeType.FULL_NODE: FullNodeRpcClient,
        NodeType.WALLET: WalletRpcClient,
    }.get(node_type)

    if rpc_client_cls is None:
        raise ValueError(f"Invalid node_type: {node_type}")

    config = load_config(root_path, "config.yaml")

    client = await rpc_client_cls.create(
        self_hostname=self_hostname,
        port=uint16(rpc_port),
        root_path=root_path,
        net_config=config,
    )

    try:
        yield client
    except Exception as e:
        logger.warning(f"Error in wallet: {e}")
    finally:
        client.close()
        await client.await_closed()


async def get_wallet_rpc_client() -> AsyncIterator[WalletRpcClient]:
    async for _ in _get_rpc_client(
        node_type=NodeType.WALLET,
        self_hostname=settings.CHIA_HOSTNAME,
        rpc_port=settings.CHIA_WALLET_RPC_PORT,
        root_path=settings.CHIA_ROOT,
    ):
        yield _


@asynccontextmanager
async def get_full_node_rpc_client() -> AsyncIterator[FullNodeRpcClient]:
    async for _ in _get_rpc_client(
        node_type=NodeType.FULL_NODE,
        self_hostname=settings.CHIA_HOSTNAME,
        rpc_port=settings.CHIA_FULL_NODE_RPC_PORT,
        root_path=settings.CHIA_ROOT,
    ):
        yield _
