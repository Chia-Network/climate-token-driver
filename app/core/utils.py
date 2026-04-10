from __future__ import annotations

import logging

from chia.consensus.constants import ConsensusConstants, replace_str_to_bytes
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.util.bech32m import encode_puzzle_hash
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.wallet.cat_wallet.cat_info import CATInfo
from chia.wallet.derive_keys import master_sk_to_wallet_sk_unhardened
from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import puzzle_for_pk
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_info import WalletInfo
from chia.wallet.wallet_request_types import (
    Addition,
    CreateSignedTransaction,
    GetPrivateKey,
    GetWallets,
)
from chia.wallet.wallet_rpc_client import WalletRpcClient
from chia_rs import G1Element, PrivateKey
from chia_rs.sized_bytes import bytes32
from chia_rs.sized_ints import uint32, uint64

from app.core.derive_keys import master_sk_to_root_sk
from app.core.types import TransactionRequest

logger = logging.getLogger("ClimateToken")


async def puzzle_hash_to_address(puzzle_hash: bytes32, wallet_client: WalletRpcClient) -> str:
    result = await wallet_client.fetch("get_network_info", {})
    prefix = result.get("network_prefix", "txch")

    return encode_puzzle_hash(puzzle_hash, prefix)


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
    asset_id: bytes32 | None,
    wallet_client: WalletRpcClient,
) -> WalletInfo | None:
    wallets_response = await wallet_client.get_wallets(GetWallets())
    wallet_infos = [WalletInfo(id=w.id, name=w.name, type=w.type, data=w.data) for w in wallets_response.wallets]

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
) -> WalletInfo | None:
    wallets_response = await wallet_client.get_wallets(GetWallets())
    wallet_infos = [WalletInfo(id=w.id, name=w.name, type=w.type, data=w.data) for w in wallets_response.wallets]

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
        CreateSignedTransaction(
            coins=transaction_request.coins,
            additions=[
                Addition(amount=a["amount"], puzzle_hash=a["puzzle_hash"], memos=a["memos"])
                for a in transaction_request.additions
            ],
            fee=uint64(transaction_request.fee),
            wallet_id=uint32(wallet_id),
        ),
        tx_config=transaction_request.tx_config,
        extra_conditions=(*transaction_request.coin_announcements, *transaction_request.puzzle_announcements),
    )

    return response.transactions
