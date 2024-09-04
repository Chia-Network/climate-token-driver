from __future__ import annotations

import asyncio
import logging
import time
from typing import List

import pytest
from chia._tests.environments.wallet import WalletStateTransition, WalletTestFramework
from chia._tests.wallet.rpc.test_wallet_rpc import WalletRpcTestEnvironment, generate_funds
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.simulator.full_node_simulator import FullNodeSimulator
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.wallet import Wallet
from chia_rs import PrivateKey

from app.core.climate_wallet.wallet import ClimateObserverWallet, ClimateWallet
from app.core.derive_keys import master_sk_to_root_sk
from app.core.types import ClimateTokenIndex, GatewayMode

logger = logging.getLogger(__name__)


async def time_out_assert_custom_interval(
    timeout: float, interval, function, value=True, *args, **kwargs  # type: ignore[no-untyped-def]
):
    __tracebackhide__ = True

    start = time.time()
    while time.time() - start < timeout:
        if asyncio.iscoroutinefunction(function):
            f_res = await function(*args, **kwargs)
        else:
            f_res = function(*args, **kwargs)
        if value == f_res:
            return None
        await asyncio.sleep(interval)
    assert False, f"Timed assertion timed out after {timeout} seconds: expected {value!r}, got {f_res!r}"


async def time_out_assert(timeout: int, function, value=True, *args, **kwargs):  # type: ignore[no-untyped-def]
    __tracebackhide__ = True
    await time_out_assert_custom_interval(timeout, 0.05, function, value, *args, **kwargs)


async def check_transactions(
    wallet_client: WalletRpcClient,
    wallet_id: int,
    transaction_records: List[TransactionRecord],
) -> None:
    for transaction_record in transaction_records:
        tx = await wallet_client.get_transaction(transaction_id=transaction_record.name)

        assert tx.confirmed_at_height != 0, f"Transaction {transaction_record.name.hex()} not found!"


async def check_balance(
    wallet_client: WalletRpcClient,
    wallet_id: int,
    amount: int,
) -> None:
    result = await wallet_client.get_wallet_balance(wallet_id=wallet_id)
    assert result["confirmed_wallet_balance"] == amount, "Target wallet CAT amount does not match!"


async def get_confirmed_balance(client: WalletRpcClient, wallet_id: int) -> int:
    return int((await client.get_wallet_balance(wallet_id))["confirmed_wallet_balance"])


@pytest.mark.parametrize(
    "org_uid, warehouse_project_id, vintage_year, amount, fee",
    [
        ("Ivern", "Rootcaller", 2016, 60, 10),
        ("Ivern", "Brushmaker", 2017, 30, 10),
        ("Ivern", "Triggerseed", 2018, 50, 10),
        ("Ivern", "Daisy!", 2019, 100, 10),
    ],
)
@pytest.mark.parametrize(
    "wallet_environments",
    [
        {
            "num_environments": 2,
            "blocks_needed": [1, 1],
            "config_overrides": {"automatically_add_unknown_cats": True},
        }
    ],
    indirect=True,
)
@pytest.mark.anyio
async def test_cat_tokenization_workflow(
    wallet_environments: WalletTestFramework,
    org_uid: str,
    warehouse_project_id: str,
    vintage_year: int,
    amount: int,
    fee: int,
) -> None:
    env_1 = wallet_environments.environments[0]
    env_2 = wallet_environments.environments[1]

    env_1.wallet_aliases = {
        "xch": 1,
        "cat": 2,
    }
    env_2.wallet_aliases = {
        "xch": 1,
        "cat": 2,
    }

    wallet_client_1: WalletRpcClient = env_1.rpc_client
    wallet_2: Wallet = env_2.xch_wallet

    fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
    result = await wallet_client_1.get_private_key(fingerprint=fingerprint)
    master_secret_key: PrivateKey = PrivateKey.from_bytes(bytes.fromhex(result["sk"]))
    root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)

    token_index = ClimateTokenIndex(
        org_uid=org_uid,
        warehouse_project_id=warehouse_project_id,
        vintage_year=vintage_year,
    )

    climate_wallet_1 = await ClimateWallet.create(
        token_index=token_index,
        root_secret_key=root_secret_key,
        wallet_client=wallet_client_1,
    )
    result = await climate_wallet_1.send_tokenization_transaction(
        to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
        amount=amount,
        fee=fee,
    )

    await wallet_environments.process_pending_states(
        [
            WalletStateTransition(
                pre_block_balance_updates={
                    "xch": {
                        "unconfirmed_wallet_balance": -amount - fee,
                        "<=#spendable_balance": -amount - fee,
                        ">=#pending_change": 1,  # any amount increase
                        "<=#max_send_amount": -amount - fee,
                        "pending_coin_removal_count": 1,
                    }
                },
                post_block_balance_updates={
                    "xch": {
                        "confirmed_wallet_balance": -amount - fee,
                        ">=#spendable_balance": 1,
                        "<=#pending_change": -1,  # any amount increase
                        ">=#max_send_amount": 1,
                        "pending_coin_removal_count": -1,
                    }
                },
            ),
            WalletStateTransition(
                pre_block_balance_updates={},
                post_block_balance_updates={
                    "cat": {
                        "init": True,
                        "confirmed_wallet_balance": amount,
                        "unconfirmed_wallet_balance": amount,
                        "spendable_balance": amount,
                        "max_send_amount": amount,
                        "unspent_coin_count": 1,
                    }
                },
            ),
        ]
    )


@pytest.mark.parametrize(
    "wallet_environments",
    [
        {
            "num_environments": 2,
            "blocks_needed": [1, 1],
            "config_overrides": {"automatically_add_unknown_cats": True},
        }
    ],
    indirect=True,
)
@pytest.mark.anyio
async def test_cat_detokenization_workflow(
    wallet_environments: WalletTestFramework,
    token_index: ClimateTokenIndex,
    amount: int = 10,
    fee: int = 10,
) -> None:
    env_1 = wallet_environments.environments[0]
    env_2 = wallet_environments.environments[1]

    env_1.wallet_aliases = {
        "xch": 1,
        "cat": 2,
    }
    env_2.wallet_aliases = {
        "xch": 1,
        "cat": 2,
    }

    wallet_client_1: WalletRpcClient = env_1.rpc_client

    wallet_client_2: WalletRpcClient = env_2.rpc_client
    wallet_2: Wallet = env_2.xch_wallet

    fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
    result = await wallet_client_1.get_private_key(fingerprint=fingerprint)
    master_secret_key: PrivateKey = PrivateKey.from_bytes(bytes.fromhex(result["sk"]))
    root_secret_key: PrivateKey = master_sk_to_root_sk(master_secret_key)

    # block:
    #   - registry: tokenization
    #   - client: create CAT wallet

    climate_wallet_1 = await ClimateWallet.create(
        token_index=token_index,
        root_secret_key=root_secret_key,
        wallet_client=wallet_client_1,
    )
    result = await climate_wallet_1.send_tokenization_transaction(
        to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
        amount=amount,
        fee=fee,
    )

    await wallet_environments.process_pending_states(
        [
            WalletStateTransition(
                pre_block_balance_updates={
                    "xch": {
                        "unconfirmed_wallet_balance": -amount - fee,
                        "<=#spendable_balance": -amount - fee,
                        ">=#pending_change": 1,  # any amount increase
                        "<=#max_send_amount": -amount - fee,
                        "pending_coin_removal_count": 1,
                    }
                },
                post_block_balance_updates={
                    "xch": {
                        "confirmed_wallet_balance": -amount - fee,
                        ">=#spendable_balance": 1,
                        "<=#pending_change": -1,  # any amount increase
                        ">=#max_send_amount": 1,
                        "pending_coin_removal_count": -1,
                    }
                },
            ),
            WalletStateTransition(
                pre_block_balance_updates={},
                post_block_balance_updates={
                    "cat": {
                        "init": True,
                        "confirmed_wallet_balance": amount,
                        "unconfirmed_wallet_balance": amount,
                        "spendable_balance": amount,
                        "max_send_amount": amount,
                        "unspent_coin_count": 1,
                    }
                },
            ),
        ]
    )

    # block:
    #   - client: create detokenization request
    #   - registry: check detokenization request
    #   - registry: sign detokenization request and push

    climate_wallet_2 = ClimateWallet(
        token_index=token_index,
        root_public_key=climate_wallet_1.root_public_key,
        mode_to_public_key=climate_wallet_1.mode_to_public_key,
        mode_to_message_and_signature=climate_wallet_1.mode_to_message_and_signature,
        wallet_client=wallet_client_2,
        constants=climate_wallet_1.constants,
    )
    result = await climate_wallet_2.create_detokenization_request(
        amount=amount,
        fee=fee,
        wallet_id=env_2.wallet_aliases["cat"],
    )
    content: str = result["content"]

    result = await ClimateWallet.parse_detokenization_request(
        content=content,
    )
    assert result["mode"] == GatewayMode.DETOKENIZATION
    assert result["amount"] == amount
    assert result["fee"] == fee
    assert result["asset_id"] == climate_wallet_1.tail_program_hash

    result = await climate_wallet_1.sign_and_send_detokenization_request(
        content=content,
    )

    # TODO: this will fail without this:
    # https://github.com/Chia-Network/chia-blockchain/blob/long_lived/vault/chia/wallet/wallet_state_manager.py#L1829-L1840
    await wallet_environments.process_pending_states(
        [
            WalletStateTransition(
                pre_block_balance_updates={
                    "xch": {
                        # Should probably review whether or not this is intentional/desired
                        "pending_coin_removal_count": 2,
                    }
                },
                post_block_balance_updates={
                    "xch": {
                        "pending_coin_removal_count": -2,
                    }
                },
            ),
            WalletStateTransition(
                pre_block_balance_updates={
                    "xch": {
                        "unconfirmed_wallet_balance": -fee,
                        "<=#spendable_balance": -fee,
                        ">=#pending_change": 1,  # any amount increase
                        "<=#max_send_amount": -fee,
                        "pending_coin_removal_count": 1,
                    },
                    "cat": {
                        "unconfirmed_wallet_balance": -amount,
                        "spendable_balance": -amount,
                        "max_send_amount": -amount,
                        "pending_coin_removal_count": 1,
                    },
                },
                post_block_balance_updates={
                    "xch": {
                        "confirmed_wallet_balance": -fee,
                        ">=#spendable_balance": 1,
                        "<=#pending_change": -1,  # any amount increase
                        ">=#max_send_amount": 1,
                        "pending_coin_removal_count": -1,
                    },
                    "cat": {
                        "confirmed_wallet_balance": -amount,
                        "unspent_coin_count": -1,
                        "pending_coin_removal_count": -1,
                    },
                },
            ),
        ]
    )


@pytest.mark.anyio
async def test_cat_permissionless_retirement_workflow(
    self,
    wallet_rpc_environment: WalletRpcTestEnvironment,  # noqa: F811
    token_index: ClimateTokenIndex,
    amount: int = 10,
    fee: int = 10,
    beneficiary_name: bytes = "Ionia".encode(),
) -> None:
    env: WalletRpcTestEnvironment = wallet_rpc_environment

    wallet_client_1: WalletRpcClient = env.wallet_1.rpc_client
    wallet_client_2: WalletRpcClient = env.wallet_2.rpc_client
    wallet_2: Wallet = env.wallet_2.wallet

    full_node_api: FullNodeSimulator = env.full_node.api
    full_node_client = env.full_node.rpc_client

    fingerprint: int = await wallet_client_1.get_logged_in_fingerprint()
    result = await wallet_client_1.get_private_key(fingerprint=fingerprint)
    master_secret_key = PrivateKey.from_bytes(bytes.fromhex(result["sk"]))
    root_secret_key = master_sk_to_root_sk(master_secret_key)

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
    result = await climate_wallet_1.send_tokenization_transaction(
        to_puzzle_hash=await wallet_2.get_new_puzzlehash(),
        amount=amount,
        fee=fee,
    )
    transaction_records = result["transaction_records"]

    result = await wallet_client_2.create_wallet_for_existing_cat(
        asset_id=climate_wallet_1.tail_program.get_tree_hash()
    )
    cat_wallet_id: int = result["wallet_id"]

    await full_node_api.process_all_wallet_transactions(
        wallet=env.wallet_1.node.wallet_state_manager.main_wallet, timeout=120
    )
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

    test_address = "This is a fake address".encode()
    result = await climate_wallet_2.send_permissionless_retirement_transaction(
        amount=amount,
        fee=fee,
        beneficiary_name=beneficiary_name,
        beneficiary_address=test_address,
        wallet_id=cat_wallet_id,
    )
    transaction_records = result["transaction_records"]

    await full_node_api.process_all_wallet_transactions(
        wallet=env.wallet_2.node.wallet_state_manager.main_wallet, timeout=120
    )
    await time_out_assert(60, get_confirmed_balance, 0, wallet_client_2, cat_wallet_id)

    # block:
    #   - observer: observe retirement activity

    climate_observer = ClimateObserverWallet(
        token_index=token_index,
        root_public_key=climate_wallet_1.root_public_key,
        full_node_client=full_node_client,
    )
    activities = await climate_observer.get_activities(mode=GatewayMode.PERMISSIONLESS_RETIREMENT)

    assert activities[0]["metadata"]["bn"] == beneficiary_name.decode()
    assert activities[0]["metadata"]["ba"] == test_address.decode()
    assert activities[0]["metadata"]["bp"] == "0x"
