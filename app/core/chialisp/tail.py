from typing import Optional

from blspy import G1Element
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32

from app.core.chialisp.load_clvm import load_clvm_locally
from app.core.types import GatewayMode

DELEGATED_TAIL_MOD = load_clvm_locally("delegated_tail_with_index.clsp")
MINT_WITH_SIGNATURE_MOD = load_clvm_locally("mint_with_signature.clsp")
MELT_ALL_BY_ANYONE_MOD = load_clvm_locally("melt_all_by_anyone.clsp")
MELT_ALL_WITH_SIGNATURE_MOD = load_clvm_locally("melt_all_with_signature.clsp")


def create_tail_program(
    public_key: G1Element,
    index: Program,
) -> Program:
    return DELEGATED_TAIL_MOD.curry(public_key, index)


def create_mint_with_signature_program(
    public_key: G1Element,
    gateway_puzzle_hash: bytes32,
) -> Program:
    return MINT_WITH_SIGNATURE_MOD.curry(public_key, gateway_puzzle_hash)


def create_melt_all_with_signature_program(
    public_key: G1Element,
    gateway_puzzle_hash: bytes32,
) -> Program:
    return MELT_ALL_WITH_SIGNATURE_MOD.curry(public_key, gateway_puzzle_hash)


def create_melt_all_by_anyone_program(
    gateway_puzzle_hash: bytes32,
) -> Program:
    return MELT_ALL_BY_ANYONE_MOD.curry(gateway_puzzle_hash)


def create_delegated_puzzle(
    mode: GatewayMode,
    gateway_puzzle_hash: bytes32,
    public_key: Optional[G1Element] = None,
) -> Program:
    if mode == GatewayMode.TOKENIZATION:
        if public_key is None:
            raise ValueError("TOKENIZATION requires specifying `public_key`!")
        delegated_puzzle = create_mint_with_signature_program(
            public_key=public_key,
            gateway_puzzle_hash=gateway_puzzle_hash,
        )

    elif mode == GatewayMode.DETOKENIZATION:
        if public_key is None:
            raise ValueError("DETOKENIZATION requires specifying `public_key`!")
        delegated_puzzle = create_melt_all_with_signature_program(
            public_key=public_key,
            gateway_puzzle_hash=gateway_puzzle_hash,
        )

    elif mode == GatewayMode.PERMISSIONLESS_RETIREMENT:
        delegated_puzzle = create_melt_all_by_anyone_program(
            gateway_puzzle_hash=gateway_puzzle_hash,
        )

    else:
        raise ValueError(f"Invalid mode {mode}!")

    return delegated_puzzle
