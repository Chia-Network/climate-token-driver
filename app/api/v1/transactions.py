from typing import Dict, List, Optional

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.byte_types import hexstr_to_bytes
from chia.wallet.cat_wallet.cat_info import CATInfo
from chia.wallet.cat_wallet.cat_utils import construct_cat_puzzle
from chia.wallet.puzzles.cat_loader import CAT_MOD
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.transaction_sorting import SortKey
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_info import WalletInfo
from fastapi import APIRouter, Depends

from app import schemas
from app.api import dependencies as deps
from app.config import ExecutionMode
from app.core.chialisp.gateway import create_gateway_puzzle, parse_gateway_spend
from app.core.types import CLIMATE_WALLET_INDEX, GatewayMode
from app.schemas.types import ChiaJsonObject
from app.utils import disallow

router = APIRouter()


@router.get(
    "/{transaction_id}",
    response_model=schemas.Transaction,
)
@disallow([ExecutionMode.EXPLORER])
async def get_transaction(
    transaction_id: str,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
):
    """Get transaction by id.

    This endpoint is to be called by the registry or the client.
    """

    transaction_record: TransactionRecord = await wallet_rpc_client.get_transaction(
        wallet_id=None,
        transaction_id=hexstr_to_bytes(transaction_id),
    )

    return schemas.Transaction(
        id=transaction_record.name,
        record=transaction_record.to_json_dict(),
    )


@router.get(
    "/",
    response_model=schemas.Transactions,
)
async def get_transactions(
    wallet_id: int,
    start: int = 0,
    end: int = 50,
    sort_key: str = "CONFIRMED_AT_HEIGHT",
    reverse: bool = False,
    to_address: Optional[str] = None,
    wallet_rpc_client: WalletRpcClient = Depends(deps.get_wallet_rpc_client),
):

    """Get transactions.

    This endpoint is to be called by the client.
    """

    transaction_records: List[
        TransactionRecord
    ] = await wallet_rpc_client.get_transactions(
        wallet_id=wallet_id,
        start=start,
        end=end,
        sort_key=SortKey[sort_key],
        reverse=reverse,
        to_address=to_address,
    )

    wallet_objs: List[ChiaJsonObject] = await wallet_rpc_client.get_wallets(
        wallet_type=WalletType.CAT,
    )
    wallet_infos: List[WalletInfo] = [
        WalletInfo.from_json_dict(wallet_obj) for wallet_obj in wallet_objs
    ]

    wallet_info: Optional[WalletInfo]
    cat_info: Optional[CATInfo] = None
    for wallet_info in wallet_infos:
        if wallet_id == wallet_info.id:
            cat_info = CATInfo.from_bytes(hexstr_to_bytes(wallet_info.data))
            break
    else:
        wallet_info = None

    if wallet_info is None:
        return schemas.Transactions(
            wallet_id=wallet_id,
            start=start,
            end=end,
            sort_key=sort_key,
            reverse=reverse,
            to_address=to_address,
            transactions=[
                transaction_record.to_json_dict()
                for transaction_record in transaction_records
            ],
        )

    gateway_puzzle: Program = create_gateway_puzzle()
    gateway_puzzle_hash: bytes32 = gateway_puzzle.get_tree_hash()
    gateway_cat_puzzle: Program = construct_cat_puzzle(
        mod_code=CAT_MOD,
        limitations_program_hash=cat_info.limitations_program_hash,
        inner_puzzle=gateway_puzzle,
    )
    gateway_cat_puzzle_hash: bytes32 = gateway_cat_puzzle.get_tree_hash()

    transactions: List[Dict] = []
    for transaction_record in transaction_records:
        if transaction_record.to_puzzle_hash != gateway_puzzle_hash:
            continue

        spend_bundle: SpendBundle = transaction_record.spend_bundle
        if spend_bundle is None:
            continue

        coin_spend: CoinSpend
        for coin_spend in spend_bundle.coin_spends:
            coin: Coin = coin_spend.coin
            if coin.puzzle_hash == gateway_cat_puzzle_hash:
                break

        else:
            raise ValueError(
                f"No coin with puzzle hash {gateway_cat_puzzle_hash.hex()}"
            )

        mode: GatewayMode
        tail_spend: CoinSpend
        (mode, tail_spend) = parse_gateway_spend(coin_spend=coin_spend, is_cat=True)

        transaction: Dict = transaction_record.to_json_dict()
        transaction["type"] = CLIMATE_WALLET_INDEX + mode.to_int()
        transaction["type_name"] = mode.name

        transactions.append(transaction)

    return schemas.Transactions(
        wallet_id=wallet_id,
        start=start,
        end=end,
        sort_key=sort_key,
        reverse=reverse,
        to_address=to_address,
        transactions=transactions,
    )
