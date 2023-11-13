import json
from typing import Any, Dict, Tuple

from blspy import G1Element, G2Element
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.byte_types import hexstr_to_bytes
from fastapi import APIRouter, Depends

from app import schemas
from app.api import dependencies as deps
from app.config import ExecutionMode
from app.core import utils
from app.core.climate_wallet.wallet import ClimateWallet
from app.core.types import ClimateTokenIndex, GatewayMode
from app.logger import logger
from app.utils import disallow

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.TokenizationTxResponse,
)
@disallow([ExecutionMode.EXPLORER, ExecutionMode.CLIENT])
async def create_tokenization_tx(
    request: schemas.TokenizationTxRequest,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
) -> schemas.TokenizationTxResponse:
    """Create and send tokenization tx.

    This endpoint is to be called by the registry.
    """

    climate_secret_key = await utils.get_climate_secret_key(wallet_client=wallet_rpc_client)

    token = request.token
    payment = request.payment

    token_index = ClimateTokenIndex(
        org_uid=token.org_uid,
        warehouse_project_id=token.warehouse_project_id,
        vintage_year=token.vintage_year,
        sequence_num=token.sequence_num,
    )
    wallet = await ClimateWallet.create(
        token_index=token_index,
        root_secret_key=climate_secret_key,
        wallet_client=wallet_rpc_client,
    )
    result = await wallet.send_tokenization_transaction(
        to_puzzle_hash=payment.to_puzzle_hash,
        amount=payment.amount,
        fee=payment.fee,
    )
    (transaction_record, *_) = result["transaction_records"]

    token_obj: Dict[str, Any] = {
        "index": wallet.token_index.name(),
        "public_key": bytes(wallet.root_public_key),
        "asset_id": wallet.tail_program_hash,
        **token.dict(),
    }

    for mode in GatewayMode:
        if wallet.mode_to_public_key is None:
            raise ValueError("Wallet mode to public key is None!")

        public_key: G1Element = wallet.mode_to_public_key[mode]

        mod_hash: bytes
        signature: G2Element
        (mod_hash, signature) = wallet.mode_to_message_and_signature[mode]

        if mode == GatewayMode.TOKENIZATION:
            token_obj["tokenization"] = schemas.TokenizationTailMetadata(
                mod_hash=mod_hash,
                public_key=bytes(public_key),
            )

        elif mode == GatewayMode.DETOKENIZATION:
            token_obj["detokenization"] = schemas.DetokenizationTailMetadata(
                mod_hash=mod_hash,
                public_key=bytes(public_key),
                signature=bytes(signature),
            )
        elif mode == GatewayMode.PERMISSIONLESS_RETIREMENT:
            token_obj["permissionless_retirement"] = schemas.PermissionlessRetirementTailMetadata(
                mod_hash=mod_hash,
                signature=bytes(signature),
            )

    token_on_chain = schemas.TokenOnChain(**token_obj)
    return schemas.TokenizationTxResponse(
        token=token_on_chain,
        token_hexstr=token_on_chain.hexstr(),
        tx=schemas.Transaction(id=transaction_record.name, record=transaction_record.to_json_dict()),
    )


@router.put(
    "/{asset_id}/detokenize",
    response_model=schemas.DetokenizationTxResponse,
)
@disallow([ExecutionMode.EXPLORER, ExecutionMode.CLIENT])
async def create_detokenization_tx(
    asset_id: str,
    request: schemas.DetokenizationTxRequest,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
) -> schemas.DetokenizationTxResponse:
    """Sign and send detokenization tx.

    This endpoint is to be called by the registry.
    """

    climate_secret_key = await utils.get_climate_secret_key(wallet_client=wallet_rpc_client)

    token: schemas.Token = request.token
    content: str = request.content

    token_index = ClimateTokenIndex(
        org_uid=token.org_uid,
        warehouse_project_id=token.warehouse_project_id,
        vintage_year=token.vintage_year,
        sequence_num=token.sequence_num,
    )
    wallet = await ClimateWallet.create(
        token_index=token_index,
        root_secret_key=climate_secret_key,
        wallet_client=wallet_rpc_client,
    )
    result = await wallet.sign_and_send_detokenization_request(content=content)
    (transaction_record, *_) = result["transaction_records"]

    return schemas.DetokenizationTxResponse(
        token=token,
        tx=schemas.Transaction(id=transaction_record.name, record=transaction_record.to_json_dict()),
    )


@router.put(
    "/{asset_id}/request-detokenization",
    response_model=schemas.DetokenizationFileResponse,
)
@disallow([ExecutionMode.EXPLORER, ExecutionMode.REGISTRY])
async def create_detokenization_file(
    asset_id: str,
    request: schemas.DetokenizationFileRequest,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
) -> schemas.DetokenizationFileResponse:
    """Create detokenization file.

    This endpoint is to be called by the client.
    """

    token = request.token
    payment = request.payment

    token_index = ClimateTokenIndex(
        org_uid=token.org_uid,
        warehouse_project_id=token.warehouse_project_id,
        vintage_year=token.vintage_year,
        sequence_num=token.sequence_num,
    )
    tail_metadata = token.detokenization

    mode_to_public_key: Dict[GatewayMode, G1Element] = {
        GatewayMode.DETOKENIZATION: G1Element.from_bytes(tail_metadata.public_key),
    }
    mode_to_message_and_signature: Dict[GatewayMode, Tuple[bytes, G2Element]] = {
        GatewayMode.DETOKENIZATION: (
            tail_metadata.mod_hash,
            G2Element.from_bytes(tail_metadata.signature),
        )
    }
    constants = await utils.get_constants(wallet_client=wallet_rpc_client)

    wallet = ClimateWallet(
        token_index=token_index,
        root_public_key=G1Element.from_bytes(token.public_key),
        mode_to_public_key=mode_to_public_key,
        mode_to_message_and_signature=mode_to_message_and_signature,
        wallet_client=wallet_rpc_client,
        constants=constants,
    )

    if wallet.tail_program_hash != hexstr_to_bytes(asset_id):
        raise ValueError(f"Asset id {asset_id} inconsistent with request body!")

    cat_wallet_info = await utils.get_cat_wallet_info_by_asset_id(
        asset_id=bytes32.from_hexstr(asset_id),
        wallet_client=wallet_rpc_client,
    )
    if cat_wallet_info is None:
        raise ValueError(f"Asset id {asset_id} not found in wallet!")

    result = await wallet.create_detokenization_request(
        amount=payment.amount,
        fee=payment.fee,
        wallet_id=cat_wallet_info.id,
    )
    content: str = result["content"]
    (transaction_record, *_) = result["transaction_records"]

    return schemas.DetokenizationFileResponse(
        token=token,
        content=content,
        tx=schemas.Transaction(id=transaction_record.name, record=transaction_record.to_json_dict()),
    )


@router.get(
    "/parse-detokenization",
    response_model=schemas.DetokenizationFileParseResponse,
)
@disallow([ExecutionMode.EXPLORER, ExecutionMode.CLIENT])
async def parse_detokenization_file(
    content: str,
) -> schemas.DetokenizationFileParseResponse:
    """Parse detokenization file.

    This endpoint is to be called by the registry.
    """

    result = await ClimateWallet.parse_detokenization_request(content=content)
    mode: GatewayMode = result["mode"]
    gateway_coin_spend: CoinSpend = result["gateway_coin_spend"]
    spend_bundle: SpendBundle = result["spend_bundle"]

    token = schemas.TokenOnChainSimple(
        asset_id=result["asset_id"],
    )
    payment = schemas.PaymentWithPayer(
        from_puzzle_hash=result["from_puzzle_hash"],
        amount=result["amount"],
        fee=result["fee"],
    )

    return schemas.DetokenizationFileParseResponse(
        mode=mode,
        token=token,
        payment=payment,
        spend_bundle=spend_bundle.to_json_dict(),
        gateway_coin_spend=gateway_coin_spend.to_json_dict(),
    )


@router.put(
    "/{asset_id}/permissionless-retire",
    response_model=schemas.PermissionlessRetirementTxResponse,
)
@disallow([ExecutionMode.EXPLORER, ExecutionMode.REGISTRY])
async def create_permissionless_retirement_tx(
    asset_id: str,
    request: schemas.PermissionlessRetirementTxRequest,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
) -> schemas.PermissionlessRetirementTxResponse:
    """Create and send permissionless retirement tx.

    This endpoint is to be called by the client.
    """

    token = request.token
    payment: schemas.RetirementPaymentWithPayer = request.payment

    token_index = ClimateTokenIndex(
        org_uid=token.org_uid,
        warehouse_project_id=token.warehouse_project_id,
        vintage_year=token.vintage_year,
        sequence_num=token.sequence_num,
    )
    tail_metadata = token.permissionless_retirement

    mode_to_message_and_signature: Dict[GatewayMode, Tuple[bytes, G2Element]] = {
        GatewayMode.PERMISSIONLESS_RETIREMENT: (
            tail_metadata.mod_hash,
            G2Element.from_bytes(tail_metadata.signature),
        )
    }
    constants = await utils.get_constants(wallet_client=wallet_rpc_client)

    wallet = ClimateWallet(
        token_index=token_index,
        root_public_key=G1Element.from_bytes(token.public_key),
        mode_to_message_and_signature=mode_to_message_and_signature,
        wallet_client=wallet_rpc_client,
        constants=constants,
    )

    if wallet.tail_program_hash != hexstr_to_bytes(asset_id):
        raise ValueError(f"Asset id {asset_id} inconsistent with request body!")

    cat_wallet_info = await utils.get_cat_wallet_info_by_asset_id(
        asset_id=bytes32.from_hexstr(asset_id),
        wallet_client=wallet_rpc_client,
    )
    if cat_wallet_info is None:
        raise ValueError(f"Asset id {asset_id} not found in wallet!")

    # Create a dictionary with the variables you want to log
    log_data = {
        "amount": payment.amount,
        "fee": payment.fee,
        "wallet_id": cat_wallet_info.id,
    }

    # Convert the dictionary to a JSON-formatted string
    log_data_json = json.dumps(log_data)

    # Log the JSON-formatted string
    logger.warning(log_data_json)

    result = await wallet.send_permissionless_retirement_transaction(
        amount=payment.amount,
        fee=payment.fee,
        beneficiary_name=payment.beneficiary_name.encode(),
        beneficiary_address=payment.beneficiary_address.encode(),
        beneficiary_puzzle_hash=payment.beneficiary_puzzle_hash,
        wallet_id=cat_wallet_info.id,
    )

    (transaction_record, *_) = result["transaction_records"]

    return schemas.PermissionlessRetirementTxResponse(
        token=token,
        tx=schemas.Transaction(id=transaction_record.name, record=transaction_record.to_json_dict()),
    )
