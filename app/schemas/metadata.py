from app.schemas.core import BaseModel


class TailMetadataBase(BaseModel):
    mod_hash: bytes


class TokenizationTailMetadata(TailMetadataBase):
    public_key: bytes


class DetokenizationTailMetadata(TailMetadataBase):
    public_key: bytes
    signature: bytes


class PermissionlessRetirementTailMetadata(TailMetadataBase):
    signature: bytes
