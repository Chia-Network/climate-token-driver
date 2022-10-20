from chia.util.byte_types import hexstr_to_bytes
from pydantic import Field

from app.schemas.core import BaseModel
from app.schemas.metadata import (
    DetokenizationTailMetadata,
    PermissionlessRetirementTailMetadata,
    TokenizationTailMetadata,
)
from app.schemas.payment import PaymentBase, PaymentWithPayee, PaymentWithPayer
from app.schemas.transaction import Transaction


class Token(BaseModel):
    org_uid: str = Field(
        example="3e70df56ff67a6806df6ad101c159363845550d1f9afd81e3e0d5a5ab51af867"
    )
    warehouse_project_id: str = Field(example="GS1")
    vintage_year: int = Field(example=2099)
    sequence_num: int = Field(example=0)


class TokenOnChainBase(Token):
    index: bytes
    public_key: bytes
    asset_id: bytes

    @classmethod
    def parse_hexstr(cls, hexstr: str) -> "TokenOnChainBase":
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


class DetokenizationFileRequest(BaseModel):
    class _TokenOnChain(TokenOnChainBase):
        detokenization: DetokenizationTailMetadata

    token: _TokenOnChain
    payment: PaymentBase


class DetokenizationFileResponse(BaseModel):
    token: Token
    content: str
    tx: Transaction


class PermissionlessRetirementTxRequest(BaseModel):
    class _TokenOnChain(TokenOnChainBase):
        permissionless_retirement: PermissionlessRetirementTailMetadata

    token: _TokenOnChain
    payment: PaymentWithPayer


class PermissionlessRetirementTxResponse(BaseModel):
    token: Token
    tx: Transaction
