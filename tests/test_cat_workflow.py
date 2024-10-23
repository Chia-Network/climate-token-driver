from __future__ import annotations

import pytest
from chia._tests.environments.wallet import WalletStateTransition, WalletTestFramework
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_request_types import GetPrivateKey
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.wallet.wallet import Wallet
from chia_rs import PrivateKey

from app.core.climate_wallet.wallet import ClimateObserverWallet, ClimateWallet
from app.core.derive_keys import master_sk_to_root_sk
from app.core.types import ClimateTokenIndex, GatewayMode


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

    fingerprint = (await wallet_client_1.get_logged_in_fingerprint()).fingerprint
    result = await wallet_client_1.get_private_key(GetPrivateKey(fingerprint=fingerprint))
    root_secret_key: PrivateKey = master_sk_to_root_sk(result.private_key.sk)

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

    fingerprint = (await wallet_client_1.get_logged_in_fingerprint()).fingerprint
    result = await wallet_client_1.get_private_key(GetPrivateKey(fingerprint=fingerprint))
    root_secret_key: PrivateKey = master_sk_to_root_sk(result.private_key.sk)

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
async def test_cat_permissionless_retirement_workflow(
    self_hostname: str,
    wallet_environments: WalletTestFramework,
    token_index: ClimateTokenIndex,
    amount: int = 10,
    fee: int = 10,
    beneficiary_name: bytes = "Ionia".encode(),
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

    fingerprint = (await wallet_client_1.get_logged_in_fingerprint()).fingerprint
    result = await wallet_client_1.get_private_key(GetPrivateKey(fingerprint=fingerprint))
    root_secret_key: PrivateKey = master_sk_to_root_sk(result.private_key.sk)

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
        wallet_id=env_2.wallet_aliases["cat"],
    )

    await wallet_environments.process_pending_states(
        [
            WalletStateTransition(),
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

    async with FullNodeRpcClient.create_as_context(
        self_hostname,
        wallet_environments.full_node.full_node.state_changed_callback.__self__.listen_port,  # a hack
        wallet_environments.full_node.full_node.root_path,
        wallet_environments.full_node.config,
    ) as client_node:
        climate_observer = ClimateObserverWallet(
            token_index=token_index,
            root_public_key=climate_wallet_1.root_public_key,
            full_node_client=client_node,
        )
        activities = await climate_observer.get_activities(mode=GatewayMode.PERMISSIONLESS_RETIREMENT)

    assert activities[0]["metadata"]["bn"] == beneficiary_name.decode()
    assert activities[0]["metadata"]["ba"] == test_address.decode()
    assert activities[0]["metadata"]["bp"] == "0x"
