# noqa: I002
# ignore the required import["from __future__ import annotations"]
# This import breaks everything - seems something to do with pydantic


from chia.util.bech32m import decode_puzzle_hash, encode_puzzle_hash
from chia.wallet.derive_keys import master_sk_to_wallet_sk, master_sk_to_wallet_sk_unhardened
from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import puzzle_hash_for_pk
from chia.wallet.wallet_request_types import GetPrivateKey
from chia.wallet.wallet_rpc_client import WalletRpcClient
from chia_rs import G1Element, PrivateKey
from chia_rs.sized_bytes import bytes32
from chia_rs.sized_ints import uint32
from fastapi import APIRouter, Depends

from app import schemas
from app.api import dependencies as deps
from app.config import ExecutionMode
from app.utils import disallow_route

router = APIRouter()


@router.get(
    "/",
    response_model=schemas.Key,
)
@disallow_route([ExecutionMode.REGISTRY, ExecutionMode.EXPLORER])
async def get_key(
    hardened: bool = False,
    derivation_index: int = 0,
    prefix: str = "bls1238",
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
) -> schemas.Key:
    fingerprint = await wallet_rpc_client.get_logged_in_fingerprint()
    assert fingerprint.fingerprint is not None

    result = await wallet_rpc_client.get_private_key(GetPrivateKey(fingerprint=fingerprint.fingerprint))

    secret_key = result.private_key.sk

    wallet_secret_key: PrivateKey
    if hardened:
        wallet_secret_key = master_sk_to_wallet_sk(secret_key, uint32(derivation_index))
    else:
        wallet_secret_key = master_sk_to_wallet_sk_unhardened(secret_key, uint32(derivation_index))

    wallet_public_key: G1Element = wallet_secret_key.get_g1()
    puzzle_hash: bytes32 = puzzle_hash_for_pk(wallet_public_key)
    wallet_address: str = encode_puzzle_hash(puzzle_hash, prefix)

    return schemas.Key(
        hex=puzzle_hash,
        bech32m=wallet_address,
    )


@router.get(
    "/parse",
    response_model=schemas.Key | None,
)
async def parse_key(
    address: str,
) -> schemas.Key | None:
    try:
        puzzle_hash: bytes = decode_puzzle_hash(address)
    except ValueError:
        return None

    return schemas.Key(
        hex=puzzle_hash,
        bech32m=address,
    )
