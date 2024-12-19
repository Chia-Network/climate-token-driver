from __future__ import annotations

import dataclasses
import enum
from typing import Any, Optional

from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.ints import uint64
from chia.wallet.conditions import CreateCoinAnnouncement, CreatePuzzleAnnouncement, ReserveFee
from chia.wallet.payment import Payment

CLIMATE_WALLET_INDEX = 2


class GatewayMode(enum.Enum):
    TOKENIZATION = "tokenization"
    DETOKENIZATION = "detokenization"
    PERMISSIONLESS_RETIREMENT = "permissionless_retirement"

    def to_int(self) -> int:
        return {
            GatewayMode.TOKENIZATION: -1,
            GatewayMode.DETOKENIZATION: 1,
            GatewayMode.PERMISSIONLESS_RETIREMENT: 0,
        }[self]


@dataclasses.dataclass
class ClimateTokenIndex:
    org_uid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int = 0

    def name(self) -> bytes32:
        to_hash: Program = Program.to(
            [
                self.org_uid,
                self.warehouse_project_id,
                self.vintage_year,
                self.sequence_num,
            ]
        )
        return to_hash.get_tree_hash()


@dataclasses.dataclass(frozen=True)
class TransactionRequest:
    coins: Optional[list[Coin]] = dataclasses.field(default=None)
    payments: list[Payment] = dataclasses.field(default_factory=list)
    coin_announcements: list[CreateCoinAnnouncement] = dataclasses.field(default_factory=list)
    puzzle_announcements: list[CreatePuzzleAnnouncement] = dataclasses.field(default_factory=list)
    fee: uint64 = dataclasses.field(default=uint64(0))

    def to_program(self) -> Program:
        conditions = []
        for payment in self.payments:
            conditions.append(payment.as_condition())

        for coin_announcement in self.coin_announcements:
            conditions.append(coin_announcement.to_program())

        for puz_announcement in self.puzzle_announcements:
            conditions.append(puz_announcement.to_program())

        if self.fee:
            conditions.append(ReserveFee(self.fee).to_program())

        ret: Program = Program.to(conditions)
        return ret

    @property
    def additions(self) -> list[dict[str, Any]]:
        additions = []
        for payment in self.payments:
            memos = [bytes.decode(memo) for memo in payment.memos]

            additions.append(
                {
                    "amount": payment.amount,
                    "puzzle_hash": payment.puzzle_hash,
                    "memos": memos,
                }
            )

        return additions
