from __future__ import annotations

import logging
from typing import Any, Optional

from chia.consensus.constants import ConsensusConstants, replace_str_to_bytes
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.rpc.wallet_request_types import GetPrivateKey
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint32, uint64
from chia.wallet.cat_wallet.cat_info import CATInfo
from chia.wallet.derive_keys import master_sk_to_wallet_sk_unhardened
from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import puzzle_for_pk
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.util.tx_config import DEFAULT_TX_CONFIG
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_info import WalletInfo
from chia_rs import G1Element, PrivateKey

from app.core.derive_keys import master_sk_to_root_sk
from app.core.types import TransactionRequest

logger = logging.getLogger("ClimateToken")


async def get_constants(
    wallet_client: WalletRpcClient,
) -> ConsensusConstants:
    result = await wallet_client.fetch("get_network_info", {})
    network_name: str = result["network_name"]

    config = load_config(
        root_path=DEFAULT_ROOT_PATH,
        filename="config.yaml",
    )
    constant_overrides = config["network_overrides"]["constants"][network_name]
    constants = replace_str_to_bytes(DEFAULT_CONSTANTS, **constant_overrides)

    return constants


async def get_climate_secret_key(
    wallet_client: WalletRpcClient,
) -> PrivateKey:
    fingerprint = await wallet_client.get_logged_in_fingerprint()
    assert fingerprint.fingerprint is not None
    result = await wallet_client.get_private_key(GetPrivateKey(fingerprint=fingerprint.fingerprint))

    master_secret_key = result.private_key.sk
    root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)
    return root_secret_key


async def get_cat_wallet_info_by_asset_id(
    asset_id: Optional[bytes32],
    wallet_client: WalletRpcClient,
) -> Optional[WalletInfo]:
    wallet_objs: list[dict[str, Any]] = await wallet_client.get_wallets()
    wallet_infos: list[WalletInfo] = [WalletInfo.from_json_dict(wallet_obj) for wallet_obj in wallet_objs]

    wallet_info: WalletInfo
    for wallet_info in wallet_infos:
        if wallet_info.type != WalletType.CAT.value:
            continue

        cat_info = CATInfo.from_bytes(bytes.fromhex(wallet_info.data))
        if asset_id == cat_info.limitations_program_hash:
            break
    else:
        return None

    return wallet_info


async def get_wallet_info_by_id(
    wallet_id: int,
    wallet_client: WalletRpcClient,
) -> Optional[WalletInfo]:
    wallet_objs: list[dict[str, Any]] = await wallet_client.get_wallets()
    wallet_infos: list[WalletInfo] = [WalletInfo.from_json_dict(wallet_obj) for wallet_obj in wallet_objs]

    wallet_info: WalletInfo
    for wallet_info in wallet_infos:
        if wallet_info.id == wallet_id:
            break
    else:
        raise ValueError(f"No wallet found for wallet ID {wallet_id}")

    return wallet_info


async def get_first_puzzle_hash(
    wallet_client: WalletRpcClient,
) -> bytes32:
    fingerprint = await wallet_client.get_logged_in_fingerprint()
    assert fingerprint.fingerprint is not None

    result = await wallet_client.get_private_key(GetPrivateKey(fingerprint=fingerprint.fingerprint))
    master_secret_key = result.private_key.sk
    wallet_secret_key: PrivateKey = master_sk_to_wallet_sk_unhardened(master_secret_key, uint32(0))
    wallet_public_key: G1Element = wallet_secret_key.get_g1()

    first_puzzle_hash: bytes32 = puzzle_for_pk(public_key=wallet_public_key).get_tree_hash()

    logger.info(f"First puzzle hash = {first_puzzle_hash.hex()}")

    return first_puzzle_hash


async def get_created_signed_transactions(
    transaction_request: TransactionRequest,
    wallet_id: int,
    wallet_client: WalletRpcClient,
) -> list[TransactionRecord]:
    response = await wallet_client.create_signed_transactions(
        coins=transaction_request.coins,
        additions=transaction_request.additions,
        fee=uint64(transaction_request.fee),
        wallet_id=wallet_id,
        tx_config=DEFAULT_TX_CONFIG,
        extra_conditions=(*transaction_request.coin_announcements, *transaction_request.puzzle_announcements),
    )

    return response.transactions
