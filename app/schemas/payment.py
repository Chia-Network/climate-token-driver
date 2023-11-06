from __future__ import annotations

from typing import Optional

from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.bech32m import decode_puzzle_hash
from pydantic import Field

from app.config import settings
from app.schemas.core import BaseModel


class PaymentBase(BaseModel):
    amount: int = Field(example=100)
    fee: int = Field(example=100, default=settings.DEFAULT_FEE)


class PaymentWithPayee(PaymentBase):
    to_address: Optional[str] = Field(
        default=None,
        example="txch1clzn09v7lapulm7j8mwx9jaqh35uh7jzjeukpv7pj50tv80zze4s5060sx",
    )

    @property
    def to_puzzle_hash(self) -> bytes32:
        if self.to_address is None:
            raise ValueError("to_address is not set")
        return decode_puzzle_hash(self.to_address)


class PaymentWithPayer(PaymentBase):
    from_puzzle_hash: bytes


class RetirementPaymentWithPayer(PaymentBase):
    beneficiary_name: str
    beneficiary_address: str

    @property
    def beneficiary_puzzle_hash(self) -> Optional[bytes32]:
        try:
            return decode_puzzle_hash(self.beneficiary_address)
        except ValueError:
            return None
