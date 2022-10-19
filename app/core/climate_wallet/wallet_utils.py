from typing import Any, Dict, List, Optional, Tuple

from blspy import AugSchemeMPL, G1Element, G2Element, PrivateKey
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import INFINITE_COST, Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode
from chia.types.spend_bundle import SpendBundle
from chia.util.condition_tools import (
    conditions_dict_for_solution,
    pkm_pairs_for_conditions_dict,
)
from chia.wallet.cat_wallet.cat_utils import (
    SpendableCAT,
    construct_cat_puzzle,
    unsigned_spend_bundle_for_spendable_cats,
)
from chia.wallet.lineage_proof import LineageProof
from chia.wallet.payment import Payment
from chia.wallet.puzzles.cat_loader import CAT_MOD

from app.core.chialisp.gateway import (
    create_gateway_announcement,
    create_gateway_puzzle,
    create_gateway_solution,
)
from app.core.chialisp.load_clvm import load_clvm_locally
from app.core.chialisp.tail import create_delegated_puzzle
from app.core.types import GatewayMode, TransactionRequest

GATEWAY_MOD = load_clvm_locally("gateway_with_conditions.clsp")


def create_gateway_request_and_spend(
    mode: GatewayMode,
    origin_coin: Coin,
    amount: int,
    tail_program: Program,
    coins: Optional[List[Coin]] = None,
    fee: int = 0,
    memos: Optional[List[bytes]] = None,
    public_key: Optional[G1Element] = None,
    from_puzzle_hash: Optional[bytes32] = None,
    to_puzzle_hash: Optional[bytes32] = None,
    key_value_pairs: Optional[List[Tuple[Any, Any]]] = None,
) -> Tuple[Program, SpendBundle]:

    tail_program_hash: bytes32 = tail_program.get_tree_hash()

    gateway_puzzle: Program = create_gateway_puzzle()
    gateway_puzzle_hash: bytes32 = gateway_puzzle.get_tree_hash()
    gateway_cat_puzzle: Program = construct_cat_puzzle(
        mod_code=CAT_MOD,
        limitations_program_hash=tail_program_hash,
        inner_puzzle=gateway_puzzle,
    )
    gateway_cat_puzzle_hash: bytes32 = gateway_cat_puzzle.get_tree_hash()

    gateway_coin = Coin(
        parent_coin_info=origin_coin.name(),
        puzzle_hash=gateway_cat_puzzle_hash,
        amount=amount,
    )

    memos = memos or []
    lineage_proof: LineageProof = LineageProof()
    gateway_payment: Payment
    if from_puzzle_hash is None:
        if mode in [GatewayMode.DETOKENIZATION, GatewayMode.PERMISSIONLESS_RETIREMENT]:
            raise ValueError(f"Mode {mode!s} requires specifying `from_puzzle_hash`!")

        gateway_payment = Payment(
            puzzle_hash=gateway_cat_puzzle_hash,
            amount=amount,
            memos=memos,
        )

    else:
        lineage_proof = LineageProof(
            parent_name=origin_coin.parent_coin_info,
            inner_puzzle_hash=from_puzzle_hash,
            amount=origin_coin.amount,
        )
        gateway_payment = Payment(
            puzzle_hash=gateway_puzzle_hash,
            amount=amount,
            memos=memos,
        )

    delegated_puzzle: Program = create_delegated_puzzle(
        mode=mode,
        gateway_puzzle_hash=gateway_puzzle_hash,
        public_key=public_key,
    )

    if key_value_pairs is None:
        if mode in [GatewayMode.PERMISSIONLESS_RETIREMENT]:
            raise ValueError(f"Mode {mode!s} requires specifying `key_value_pairs`!")

    delegated_solution = Program.to(key_value_pairs)
    tail_solution = Program.to([delegated_puzzle, delegated_solution])

    extra_delta: int = 0
    conditions: List[List] = []

    conditions.append(
        [ConditionOpcode.CREATE_COIN, None, -113, tail_program, tail_solution]
    )

    if to_puzzle_hash is None:
        if mode in [GatewayMode.TOKENIZATION]:
            raise ValueError(f"Mode {mode!s} requires specifying `to_puzzle_hash`!")

        extra_delta = -amount

    else:
        conditions.append(
            [ConditionOpcode.CREATE_COIN, to_puzzle_hash, amount, [to_puzzle_hash]]
        )

    conditions_program = Program.to(conditions)
    gateway_announcement = create_gateway_announcement(
        coin=gateway_coin,
        conditions_program=conditions_program,
    )
    transaction_request = TransactionRequest(
        coins=coins,
        payments=[gateway_payment],
        coin_announcements=[gateway_announcement],
        fee=fee,
    )

    gateway_solution: Program = create_gateway_solution(
        conditions_program=conditions_program,
    )
    spendable_cat = SpendableCAT(
        coin=gateway_coin,
        limitations_program_hash=tail_program_hash,
        lineage_proof=lineage_proof,
        extra_delta=extra_delta,
        inner_puzzle=gateway_puzzle,
        inner_solution=gateway_solution,
    )
    unsigned_spend_bundle = unsigned_spend_bundle_for_spendable_cats(
        CAT_MOD, [spendable_cat]
    )
    unsigned_coin_spend: CoinSpend = unsigned_spend_bundle.coin_spends[0]

    return (transaction_request, unsigned_coin_spend)


def create_gateway_signature(
    coin_spend: CoinSpend,
    agg_sig_additional_data: bytes,
    public_key_to_secret_key: Optional[Dict[bytes, PrivateKey]] = None,
    public_key_message_to_signature: Optional[
        Dict[Tuple[bytes, bytes], G2Element]
    ] = None,
    allow_missing: bool = False,
) -> G2Element:

    if public_key_to_secret_key is None:
        public_key_to_secret_key = {}

    if public_key_message_to_signature is None:
        public_key_message_to_signature = {}

    (_, conditions_dict, _) = conditions_dict_for_solution(
        coin_spend.puzzle_reveal,
        coin_spend.solution,
        INFINITE_COST,
    )

    signatures: List[G2Element] = []
    for (public_key, message) in pkm_pairs_for_conditions_dict(
        conditions_dict,
        coin_spend.coin.name(),
        agg_sig_additional_data,
    ):

        signature: Optional[G2Element] = None

        secret_key: PrivateKey = public_key_to_secret_key.get(public_key)
        if secret_key is not None:
            signature = AugSchemeMPL.sign(secret_key, message)

        if signature is None:
            signature = public_key_message_to_signature.get((public_key, message))

        if signature is None:
            if allow_missing:
                continue
            else:
                raise ValueError(
                    f"Cannot sign for key {public_key.hex()} and message {message.hex()}"
                )

        signatures.append(signature)

    return AugSchemeMPL.aggregate(signatures)
