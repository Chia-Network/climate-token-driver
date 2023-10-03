import dataclasses
import enum
from typing import Dict, List, Optional

from chia.types.announcement import Announcement
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.condition_opcodes import ConditionOpcode
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
class ClimateTokenIndex(object):
    org_uid: str
    warehouse_project_id: str
    vintage_year: int
    sequence_num: int = 0

    def name(self) -> bytes32:
        return Program.to(
            [
                self.org_uid,
                self.warehouse_project_id,
                self.vintage_year,
                self.sequence_num,
            ]
        ).get_tree_hash()


@dataclasses.dataclass(frozen=True)
class TransactionRequest(object):
    coins: Optional[List[Coin]] = dataclasses.field(default=None)
    payments: List[Payment] = dataclasses.field(default_factory=list)
    coin_announcements: List[Announcement] = dataclasses.field(default_factory=list)
    puzzle_announcements: List[Announcement] = dataclasses.field(default_factory=list)
    fee: int = dataclasses.field(default=0)

    def to_program(self) -> Program:
        conditions: List[List] = []
        for payment in self.payments:
            conditions.append(
                [ConditionOpcode.CREATE_COIN] + payment.as_condition_args()
            )

        for announcement in self.coin_announcements:
            conditions.append(
                [ConditionOpcode.ASSERT_COIN_ANNOUNCEMENT, announcement.name()]
            )

        for announcement in self.puzzle_announcements:
            conditions.append(
                [ConditionOpcode.ASSERT_PUZZLE_ANNOUNCEMENT, announcement.name()]
            )

        if self.fee:
            conditions.append([ConditionOpcode.RESERVE_FEE, self.fee])

        return Program.to(conditions)

    @property
    def additions(self) -> List[Dict]:
        additions: List[Dict] = []
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
