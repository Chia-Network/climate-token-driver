from typing import Optional, Tuple

from chia.types.announcement import Announcement
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode

from app.core.chialisp.load_clvm import load_clvm_locally
from app.core.chialisp.tail import (
    DELEGATED_TAIL_MOD,
    MELT_ALL_BY_ANYONE_MOD,
    MELT_ALL_WITH_SIGNATURE_MOD,
    MINT_WITH_SIGNATURE_MOD,
)
from app.core.types import GatewayMode

GATEWAY_MOD = load_clvm_locally("gateway_with_conditions.clsp")


def create_gateway_puzzle() -> Program:
    return GATEWAY_MOD


def create_gateway_solution(
    conditions_program: Program,
) -> Program:

    return Program.to([conditions_program])


def create_gateway_announcement(
    coin: Coin,
    conditions_program: Program,
) -> Announcement:

    return Announcement(
        origin_info=coin.name(),
        message=conditions_program.get_tree_hash(),
    )


def parse_gateway_spend(
    coin_spend: CoinSpend,
    is_cat: bool = True,
) -> Tuple[GatewayMode, CoinSpend]:

    puzzle: Program = coin_spend.puzzle_reveal.to_program()
    solution: Program = coin_spend.solution.to_program()
    coin: Coin = coin_spend.coin

    if is_cat:
        (_, puzzle_args) = puzzle.uncurry()

        puzzle = puzzle_args.at("rrf")
        solution = solution.at("f")

    conditions: Program = puzzle.run(solution)

    tail_program: Optional[Program] = None
    for condition in conditions.as_iter():
        opcode: bytes = condition.at("f").as_atom()
        if opcode != ConditionOpcode.CREATE_COIN:
            continue

        amount: int = condition.at("rrf").as_int()

        if amount == -113:
            tail_program: Program = condition.at("rrrf")
            tail_solution: Program = condition.at("rrrrf")
            break
    else:
        raise ValueError(f"No TAIL found!")

    (tail_program_mod, _) = tail_program.uncurry()
    if tail_program_mod != DELEGATED_TAIL_MOD:
        raise ValueError("TAIL mod {tail_program_mod.get_tree_hash().hex()} invalid!")

    delegated_puzzle: Program = tail_solution.at("f")
    (delegated_puzzle_mod, _) = delegated_puzzle.uncurry()

    mode: Optional[GatewayMode] = None
    if delegated_puzzle_mod == MINT_WITH_SIGNATURE_MOD:
        mode = GatewayMode.TOKENIZATION
    elif delegated_puzzle_mod == MELT_ALL_BY_ANYONE_MOD:
        mode = GatewayMode.PERMISSIONLESS_RETIREMENT
    elif delegated_puzzle_mod == MELT_ALL_WITH_SIGNATURE_MOD:
        mode = GatewayMode.DETOKENIZATION
    else:
        puzzle_hash: bytes32 = delegated_puzzle_mod.get_tree_hash()
        raise ValueError(f"Invalid delegated puzzle with hash {puzzle_hash.hex()}")

    tail_spend = CoinSpend(
        coin=coin,
        puzzle_reveal=tail_program,
        solution=tail_solution,
    )

    return (mode, tail_spend)
