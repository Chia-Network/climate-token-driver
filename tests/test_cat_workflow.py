import logging
from typing import Dict, List

import pytest
from blspy import PrivateKey
from chia.consensus.constants import ConsensusConstants
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.server import ChiaServer
from chia.simulator.full_node_simulator import FullNodeSimulator
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.spend_bundle import SpendBundle
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.wallet import Wallet
from chia.wallet.wallet_node import WalletNode

from app.core.climate_wallet.wallet import ClimateObserverWallet, ClimateWallet
from app.core.derive_keys import master_sk_to_root_sk
from app.core.types import ClimateTokenIndex, GatewayMode
from app.core.utils import get_first_puzzle_hash
from tests.wallet.rpc.test_wallet_rpc import wallet_rpc_environment  # noqa
from tests.wallet.rpc.test_wallet_rpc import (
    WalletRpcTestEnvironment,
    farm_transaction,
    farm_transaction_block,
    generate_funds,
)

logger = logging.getLogger(__name__)


async def check_transactions(
    wallet_client: WalletRpcClient,
    wallet_id: int,
    transaction_records: List[TransactionRecord],
) -> None:

    for transaction_record in transaction_records:
        tx = await wallet_client.get_transaction(
            wallet_id=wallet_id, transaction_id=transaction_record.name
        )

        assert (
            tx.confirmed_at_height != 0
        ), "Transaction {transaction_record.name.hex()} not found!"


async def check_balance(
    wallet_client: WalletRpcClient,
    wallet_id: int,
    amount: int,
) -> None:

    result: Dict = await wallet_client.get_wallet_balance(wallet_id=wallet_id)
    assert (
        result["confirmed_wallet_balance"] == amount
    ), "Target wallet CAT amount does not match!"


class TestCATWorkflow:
    @pytest.mark.parametrize(
        "org_uid, warehouse_project_id, vintage_year, amount, fee",
        [
            ("Ivern", "Rootcaller", 2016, 60, 10),
            ("Ivern", "Brushmaker", 2017, 30, 10),
            ("Ivern", "Triggerseed", 2018, 50, 10),
            ("Ivern", "Daisy!", 2019, 100, 10),
        ],
    )
    @pytest.mark.asyncio
    async def test_cat_tokenization_workflow(
        self,
        wallet_rpc_environment: WalletRpcTestEnvironment,
        org_uid: str,
        warehouse_project_id: str,
        vintage_year: int,
        amount: int,
        fee: int,
    ) -> None:

        env: WalletRpcTestEnvironment = wallet_rpc_environment

        wallet_node_1: WalletNode = env.wallet_1.node
        wallet_client_1: WalletRpcClient = env.wallet_1.rpc_client

        wallet_client_2: WalletRpcClient = env.wallet_2.rpc_client
        wallet_2: Wallet = env.wallet_2.wallet

        full_node_api: FullNodeSimulator = env.full_node.api

        fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
        result: Dict = await wallet_client_1.get_private_key(fingerprint=fingerprint)
        master_secret_key: PrivateKey = PrivateKey.from_bytes(
            bytes.fromhex(result["sk"])
        )
        root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)

        token_index = ClimateTokenIndex(
            org_uid=org_uid,
            warehouse_project_id=warehouse_project_id,
            vintage_year=vintage_year,
        )

        # block:
        #   - registry: fund deposit

        await generate_funds(full_node_api, env.wallet_1)

        # block:
        #   - registry: tokenization

        climate_wallet_1 = await ClimateWallet.create(
            token_index=token_index,
            root_secret_key=root_secret_key,
            wallet_client=wallet_client_1,
        )
        result: Dict = await climate_wallet_1.send_tokenization_transaction(
            to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
            amount=amount,
            fee=fee,
        )
        spend_bundle: SpendBundle = result["spend_bundle"]
        transaction_records: List[TransactionRecord] = result["transaction_records"]

        await farm_transaction(full_node_api, wallet_node_1, spend_bundle)
        await check_transactions(wallet_client_1, 1, transaction_records)

        # block:
        #   - client: create CAT wallet

        result: List[Dict] = await wallet_client_2.get_stray_cats()
        asset_id = bytes32.fromhex(result[0]["asset_id"])
        result: Dict = await wallet_client_2.create_wallet_for_existing_cat(
            asset_id=asset_id
        )
        cat_wallet_id: int = result["wallet_id"]

        await farm_transaction_block(full_node_api, wallet_node_1)
        await check_balance(wallet_client_2, cat_wallet_id, amount)

    @pytest.mark.asyncio
    async def test_cat_detokenization_workflow(
        self,
        wallet_rpc_environment: WalletRpcTestEnvironment,
        token_index: ClimateTokenIndex,
        amount: int = 10,
        fee: int = 10,
    ) -> None:

        env: WalletRpcTestEnvironment = wallet_rpc_environment

        wallet_node_1: WalletNode = env.wallet_1.node
        wallet_client_1: WalletRpcClient = env.wallet_1.rpc_client

        wallet_client_2: WalletRpcClient = env.wallet_2.rpc_client
        wallet_2: Wallet = env.wallet_2.wallet

        full_node_api: FullNodeSimulator = env.full_node.api

        fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
        result: Dict = await wallet_client_1.get_private_key(fingerprint=fingerprint)
        master_secret_key: PrivateKey = PrivateKey.from_bytes(
            bytes.fromhex(result["sk"])
        )
        root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)
        constants: ConsensusConstants = full_node_api.full_node.constants

        # block: initial fund deposits

        await generate_funds(full_node_api, env.wallet_1)
        await generate_funds(full_node_api, env.wallet_2)

        # block:
        #   - registry: tokenization
        #   - client: create CAT wallet

        climate_wallet_1 = await ClimateWallet.create(
            token_index=token_index,
            root_secret_key=root_secret_key,
            wallet_client=wallet_client_1,
        )
        result: Dict = await climate_wallet_1.send_tokenization_transaction(
            to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
            amount=amount,
            fee=fee,
        )
        spend_bundle: SpendBundle = result["spend_bundle"]
        transaction_records: List[TransactionRecord] = result["transaction_records"]

        result: Dict = await wallet_client_2.create_wallet_for_existing_cat(
            asset_id=climate_wallet_1.tail_program.get_tree_hash()
        )
        cat_wallet_id: int = result["wallet_id"]

        await farm_transaction(full_node_api, wallet_node_1, spend_bundle)
        await check_transactions(wallet_client_1, 1, transaction_records)

        # block:
        #   - client: create detokenization request
        #   - registry: sign detokenization request and push

        climate_wallet_2 = ClimateWallet(
            token_index=token_index,
            root_public_key=climate_wallet_1.root_public_key,
            mode_to_public_key=climate_wallet_1.mode_to_public_key,
            mode_to_message_and_signature=climate_wallet_1.mode_to_message_and_signature,
            wallet_client=wallet_client_2,
            constants=climate_wallet_1.constants,
        )
        result: Dict = await climate_wallet_2.create_detokenization_request(
            amount=amount,
            fee=fee,
            wallet_id=cat_wallet_id,
        )
        content: str = result["content"]
        transaction_records: List[TransactionRecord] = result["transaction_records"]

        result: Dict = await climate_wallet_1.sign_and_send_detokenization_request(
            content=content,
        )
        spend_bundle: SpendBundle = result["spend_bundle"]

        await farm_transaction(full_node_api, wallet_node_1, spend_bundle)
        await check_transactions(wallet_client_2, cat_wallet_id, transaction_records)
        await check_balance(wallet_client_2, cat_wallet_id, 0)

    @pytest.mark.asyncio
    async def test_cat_permissionless_retirement_workflow(
        self,
        wallet_rpc_environment: WalletRpcTestEnvironment,
        token_index: ClimateTokenIndex,
        amount: int = 10,
        fee: int = 10,
        beneficiary_name: bytes = b"Ionia",
    ) -> None:

        env: WalletRpcTestEnvironment = wallet_rpc_environment

        wallet_node_1: WalletNode = env.wallet_1.node
        wallet_client_1: WalletRpcClient = env.wallet_1.rpc_client

        wallet_node_2: WalletNode = env.wallet_2.node
        wallet_client_2: WalletRpcClient = env.wallet_2.rpc_client
        wallet_2: Wallet = env.wallet_2.wallet

        full_node_api: FullNodeSimulator = env.full_node.api
        full_node_client: ChiaServer = env.full_node.rpc_client

        fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
        result: Dict = await wallet_client_1.get_private_key(fingerprint=fingerprint)
        master_secret_key: PrivateKey = PrivateKey.from_bytes(
            bytes.fromhex(result["sk"])
        )
        root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)
        constants: ConsensusConstants = full_node_api.full_node.constants

        # block: initial fund deposits

        await generate_funds(full_node_api, env.wallet_1)
        await generate_funds(full_node_api, env.wallet_2)

        # block:
        #   - registry: tokenization
        #   - client: create CAT wallet

        climate_wallet_1 = await ClimateWallet.create(
            token_index=token_index,
            root_secret_key=root_secret_key,
            wallet_client=wallet_client_1,
        )
        result: Dict = await climate_wallet_1.send_tokenization_transaction(
            to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
            amount=amount,
            fee=fee,
        )
        spend_bundle: SpendBundle = result["spend_bundle"]
        transaction_records: List[TransactionRecord] = result["transaction_records"]

        result: Dict = await wallet_client_2.create_wallet_for_existing_cat(
            asset_id=climate_wallet_1.tail_program.get_tree_hash()
        )
        cat_wallet_id: int = result["wallet_id"]

        await farm_transaction(full_node_api, wallet_node_1, spend_bundle)
        await check_transactions(wallet_client_1, 1, transaction_records)

        # block:
        #   - client: create permissionless retirement transaction

        climate_wallet_2 = ClimateWallet(
            token_index=token_index,
            root_public_key=climate_wallet_1.root_public_key,
            mode_to_public_key=climate_wallet_1.mode_to_public_key,
            mode_to_message_and_signature=climate_wallet_1.mode_to_message_and_signature,
            wallet_client=wallet_client_2,
            constants=climate_wallet_1.constants,
        )
        result: Dict = (
            await climate_wallet_2.send_permissionless_retirement_transaction(
                amount=amount,
                fee=fee,
                beneficiary_name=beneficiary_name,
                wallet_id=cat_wallet_id,
            )
        )
        spend_bundle: SpendBundle = result["spend_bundle"]
        transaction_records: List[TransactionRecord] = result["transaction_records"]

        await farm_transaction(full_node_api, wallet_node_2, spend_bundle)
        await check_transactions(wallet_client_2, cat_wallet_id, transaction_records)
        await check_balance(wallet_client_2, cat_wallet_id, 0)

        # block:
        #   - observer: observe retirement activity

        climate_observer = ClimateObserverWallet(
            token_index=token_index,
            root_public_key=climate_wallet_1.root_public_key,
            full_node_client=full_node_client,
        )
        activities: List[Dict] = await climate_observer.get_activities(
            mode=GatewayMode.PERMISSIONLESS_RETIREMENT
        )

        assert activities[0]["metadata"][b"bn"] == beneficiary_name
        assert activities[0]["metadata"][b"bp"] == await get_first_puzzle_hash(
            wallet_client_2
        )
