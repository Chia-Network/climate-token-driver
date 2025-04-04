from __future__ import annotations

from chia.util.byte_types import hexstr_to_bytes
from pydantic import Field

from app.core.types import GatewayMode
from app.schemas.core import BaseModel
from app.schemas.metadata import (
    DetokenizationTailMetadata,
    PermissionlessRetirementTailMetadata,
    TokenizationTailMetadata,
)
from app.schemas.payment import PaymentBase, PaymentWithPayee, PaymentWithPayer, RetirementPaymentWithPayer
from app.schemas.transaction import Transaction
from app.schemas.types import ChiaJsonObject


class Token(BaseModel):
    org_uid: str = Field(example="3e70df56ff67a6806df6ad101c159363845550d1f9afd81e3e0d5a5ab51af867")
    warehouse_project_id: str = Field(example="GS1")
    vintage_year: int = Field(example=2099)
    sequence_num: int = Field(example=0)


class TokenOnChainSimple(BaseModel):
    asset_id: bytes


class TokenOnChainBase(Token):
    index: bytes
    public_key: bytes
    asset_id: bytes

    @classmethod
    def parse_hexstr(cls, hexstr: str) -> TokenOnChainBase:
        return cls.parse_raw(hexstr_to_bytes(hexstr).decode())

    def hexstr(self) -> str:
        return self.json().encode().hex()


class TokenOnChain(TokenOnChainBase):
    tokenization: TokenizationTailMetadata
    detokenization: DetokenizationTailMetadata
    permissionless_retirement: PermissionlessRetirementTailMetadata


class TokenizationTxRequest(BaseModel):
    token: Token
    payment: PaymentWithPayee


class TokenizationTxResponse(BaseModel):
    token: TokenOnChain
    token_hexstr: str
    tx: Transaction


class DetokenizationTxRequest(BaseModel):
    token: TokenOnChainBase
    content: str


class DetokenizationTxResponse(BaseModel):
    token: Token
    tx: Transaction


class DetokenizationFileParseResponse(BaseModel):
    mode: GatewayMode
    token: TokenOnChainSimple
    payment: PaymentWithPayer
    spend_bundle: ChiaJsonObject
    gateway_coin_spend: ChiaJsonObject


class _TokenOnChain_Detokenize(TokenOnChainBase):
    detokenization: DetokenizationTailMetadata


class DetokenizationFileRequest(BaseModel):
    token: _TokenOnChain_Detokenize
    payment: PaymentBase


class DetokenizationFileResponse(BaseModel):
    token: Token
    content: str
    tx: Transaction


class _TokenOnChain_Permissionless(TokenOnChainBase):
    permissionless_retirement: PermissionlessRetirementTailMetadata


class PermissionlessRetirementTxRequest(BaseModel):
    token: _TokenOnChain_Permissionless
    payment: RetirementPaymentWithPayer


class PermissionlessRetirementTxResponse(BaseModel):
    token: Token
    tx: Transaction
