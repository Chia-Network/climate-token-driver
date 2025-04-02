from __future__ import annotations

import dataclasses
import logging
import time
from collections.abc import Iterator
from typing import Any, Optional, Union

from chia.consensus.constants import ConsensusConstants
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.rpc.wallet_request_types import PushTransactions
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import CoinRecord
from chia.types.coin_spend import CoinSpend, make_spend
from chia.types.spend_bundle import SpendBundle, estimate_fees
from chia.util.bech32m import bech32_decode, bech32_encode, convertbits
from chia.util.ints import uint32, uint64
from chia.wallet.cat_wallet.cat_utils import (
    CAT_MOD,
    construct_cat_puzzle,
    get_innerpuzzle_from_puzzle,
    match_cat_puzzle,
)
from chia.wallet.conditions import ConditionValidTimes
from chia.wallet.payment import Payment
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.uncurried_puzzle import uncurry_puzzle
from chia.wallet.util.compute_memos import compute_memos
from chia.wallet.util.tx_config import DEFAULT_TX_CONFIG
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_spend_bundle import WalletSpendBundle
from chia_rs import AugSchemeMPL, G1Element, G2Element, PrivateKey

from app.core.chialisp.gateway import create_gateway_puzzle, parse_gateway_spend
from app.core.chialisp.tail import create_delegated_puzzle, create_tail_program
from app.core.climate_wallet.wallet_utils import create_gateway_request_and_spend, create_gateway_signature
from app.core.derive_keys import root_sk_to_gateway_sk
from app.core.types import CLIMATE_WALLET_INDEX, ClimateTokenIndex, GatewayMode, TransactionRequest
from app.core.utils import get_constants, get_created_signed_transactions, get_first_puzzle_hash, get_wallet_info_by_id

logger = logging.getLogger("ClimateToken")


@dataclasses.dataclass
class ClimateWalletBase:
    token_index: ClimateTokenIndex
    root_public_key: G1Element

    @property
    def token_index_hash(self) -> bytes32:
        return self.token_index.name()

    @property
    def tail_program(self) -> Program:
        return create_tail_program(
            public_key=self.root_public_key,
            index=Program.to(self.token_index_hash),
        )

    @property
    def tail_program_hash(self) -> bytes32:
        return self.tail_program.get_tree_hash()


@dataclasses.dataclass
class ClimateWallet(ClimateWalletBase):
    mode_to_public_key: Optional[dict[GatewayMode, G1Element]] = dataclasses.field(default=None, kw_only=True)
    mode_to_secret_key: Optional[dict[GatewayMode, PrivateKey]] = dataclasses.field(default=None, kw_only=True)
    mode_to_message_and_signature: dict[GatewayMode, tuple[bytes, G2Element]]

    wallet_client: WalletRpcClient
    constants: ConsensusConstants

    @classmethod
    async def create(
        cls,
        token_index: ClimateTokenIndex,
        root_secret_key: PrivateKey,
        wallet_client: WalletRpcClient,
    ) -> ClimateWallet:
        root_public_key: G1Element = root_secret_key.get_g1()
        token_index_hash: bytes32 = token_index.name()
        tail_program = create_tail_program(public_key=root_public_key, index=Program.to(token_index_hash))
        tail_program_hash: bytes32 = tail_program.get_tree_hash()

        logger.info("Creating climate wallet for")
        logger.info(f"  - Token index: {token_index_hash.hex()}")
        logger.info(f"  - Asset ID: {tail_program_hash.hex()}")

        mode_to_public_key: dict[GatewayMode, G1Element] = {}
        mode_to_secret_key: dict[GatewayMode, PrivateKey] = {}
        mode_to_message_and_signature: dict[GatewayMode, tuple[bytes, G2Element]] = {}
        for mode in GatewayMode:
            secret_key: PrivateKey = root_sk_to_gateway_sk(root_secret_key)
            public_key: G1Element = secret_key.get_g1()

            gateway_puzzle: Program = create_gateway_puzzle()
            gateway_puzzle_hash: bytes32 = gateway_puzzle.get_tree_hash()

            delegated_puzzle: Program = create_delegated_puzzle(
                mode=mode,
                gateway_puzzle_hash=gateway_puzzle_hash,
                public_key=public_key,
            )
            delegated_puzzle_hash: bytes32 = delegated_puzzle.get_tree_hash()
            message: bytes32 = Program.to([token_index_hash, delegated_puzzle]).get_tree_hash()
            signature: G2Element = AugSchemeMPL.sign(root_secret_key, message)

            mode_to_public_key[mode] = secret_key.get_g1()
            mode_to_secret_key[mode] = secret_key
            mode_to_message_and_signature[mode] = (message, signature)

            logger.info(f"Signing delegated tail for mode `{mode.name}`:")
            logger.info(f"  - Public key: {bytes(public_key).hex()}")
            logger.info(f"  - Delegated puzzle hash: {delegated_puzzle_hash.hex()}")
            logger.info(f"  - Message: {message.hex()}")
            logger.info(f"  - Signature: {bytes(signature).hex()}")

        constants = await get_constants(wallet_client=wallet_client)

        return ClimateWallet(
            token_index=token_index,
            root_public_key=root_public_key,
            mode_to_public_key=mode_to_public_key,
            mode_to_secret_key=mode_to_secret_key,
            mode_to_message_and_signature=mode_to_message_and_signature,
            wallet_client=wallet_client,
            constants=constants,
        )

    @property
    def is_registry(self) -> bool:
        return self.mode_to_secret_key is not None

    @property
    def has_wallet_client(self) -> bool:
        return self.wallet_client is not None

    @property
    def delegated_signatures(self) -> dict[tuple[G1Element, bytes], G2Element]:
        return {
            (self.root_public_key, message): signature
            for (
                mode,
                (message, signature),
            ) in self.mode_to_message_and_signature.items()
        }

    def check_user(
        self,
        is_registry: bool,
    ) -> None:
        if is_registry != self.is_registry:
            raise ValueError("Incorrect user!")

        if is_registry:
            if self.mode_to_public_key is None:
                raise ValueError("No public keys provided for the registry!")

            if self.mode_to_secret_key is None:
                raise ValueError("No secret keys provided for the registry!")

    async def check_wallet(
        self,
        wallet_id: int,
        wallet_type: WalletType,
    ) -> None:
        if not self.has_wallet_client:
            raise ValueError("No wallet client provided!")

        wallet_info = await get_wallet_info_by_id(
            wallet_id=wallet_id,
            wallet_client=self.wallet_client,
        )

        if wallet_info is None:
            raise ValueError(f"No wallet found for wallet ID {wallet_id}")

        if wallet_info.type != wallet_type.value:
            raise ValueError(f"Incorrect wallet type {wallet_info.type}!")

    async def _create_transaction(
        self,
        mode: GatewayMode,
        coins: list[Coin],
        origin_coin: Coin,
        amount: int,
        fee: int = 0,
        from_puzzle_hash: Optional[bytes32] = None,
        to_puzzle_hash: Optional[bytes32] = None,
        key_value_pairs: Optional[list[tuple[Any, Any]]] = None,
        gateway_public_key: Optional[G1Element] = None,
        public_key_to_secret_key: Optional[dict[G1Element, PrivateKey]] = None,
        allow_missing_signature: bool = False,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        unsigned_gateway_coin_spend: CoinSpend
        signature: G2Element
        memos: list[bytes] = []

        (
            transaction_request,
            unsigned_gateway_coin_spend,
        ) = create_gateway_request_and_spend(
            mode=mode,
            coins=coins,
            amount=uint64(amount),
            fee=fee,
            memos=memos,
            origin_coin=origin_coin,
            tail_program=self.tail_program,
            public_key=gateway_public_key,
            from_puzzle_hash=from_puzzle_hash,
            to_puzzle_hash=to_puzzle_hash,
            key_value_pairs=key_value_pairs,
        )
        signature = create_gateway_signature(
            unsigned_gateway_coin_spend,
            agg_sig_additional_data=self.constants.AGG_SIG_ME_ADDITIONAL_DATA,
            public_key_to_secret_key=public_key_to_secret_key,
            public_key_message_to_signature=self.delegated_signatures,
            allow_missing=allow_missing_signature,
        )
        gateway_spend_bundle = SpendBundle(
            coin_spends=[unsigned_gateway_coin_spend],
            aggregated_signature=signature,
        )

        transactions = await get_created_signed_transactions(
            transaction_request=transaction_request,
            wallet_id=wallet_id,
            wallet_client=self.wallet_client,
        )
        new_txs = []
        for tx in transactions:
            if unsigned_gateway_coin_spend.coin in tx.additions:
                spend_bundle = WalletSpendBundle.aggregate(
                    [gateway_spend_bundle] + ([] if tx.spend_bundle is None else [tx.spend_bundle])
                )
                additions = [
                    add for add in tx.additions if add != unsigned_gateway_coin_spend.coin
                ] + gateway_spend_bundle.additions()
            else:
                spend_bundle = WalletSpendBundle.aggregate([] if tx.spend_bundle is None else [tx.spend_bundle])
                additions = tx.additions
            removals = [rem for rem in tx.removals if rem not in additions]
            new_tx = dataclasses.replace(
                tx,
                spend_bundle=spend_bundle,
                additions=additions,
                removals=removals,
                type=uint32(CLIMATE_WALLET_INDEX + mode.to_int()),
                name=spend_bundle.name(),
                memos=list(compute_memos(spend_bundle).items()),
            )
            new_txs.append(new_tx)

        return {
            "transaction_id": new_txs[0].name,
            "transaction_records": new_txs,
            "spend_bundle": SpendBundle.aggregate([tx.spend_bundle for tx in new_txs if tx.spend_bundle is not None]),
        }

    async def _create_client_transaction(
        self,
        mode: GatewayMode,
        amount: int,
        fee: int = 0,
        gateway_public_key: Optional[G1Element] = None,
        gateway_key_values: Optional[dict[str, Any]] = None,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        self.check_user(is_registry=False)
        await self.check_wallet(wallet_id=wallet_id, wallet_type=WalletType.CAT)

        coins: list[Coin] = await self.wallet_client.select_coins(
            amount=amount,
            wallet_id=wallet_id,
            coin_selection_config=DEFAULT_TX_CONFIG.coin_selection_config,
        )
        if not len(coins):
            raise ValueError("Insufficient balance!")

        origin_coin: Coin = coins[0]

        logger.info(f"Creating transaction for mode {mode.name}:")
        logger.info(f"  - Amount: {amount}")
        logger.info(f"  - Fee: {fee}")

        if gateway_key_values:
            logger.info("  - Announcements:")
            for key, value in gateway_key_values.items():
                logger.info(f"    - {key}: {value}")

        transaction_request: TransactionRequest

        # this is a hack to get inner puzzle hash for `origin_coin`

        transaction_request = TransactionRequest(
            coins=[origin_coin],
            payments=[
                Payment(
                    puzzle_hash=bytes32(b"0" * 32),
                    amount=uint64(origin_coin.amount),
                    memos=[],
                )
            ],
            fee=uint64(0),
        )
        transactions = await get_created_signed_transactions(
            transaction_request=transaction_request,
            wallet_id=wallet_id,
            wallet_client=self.wallet_client,
        )
        if len(transactions) != 1:
            raise ValueError(f"Transaction record has unexpected length {len(transactions)}!")

        transaction_record = transactions[0]
        if transaction_record.spend_bundle is None:
            raise ValueError("No spend bundle created!")
        coin_spend: CoinSpend = transaction_record.spend_bundle.coin_spends[0]
        puzzle: Program = coin_spend.puzzle_reveal.to_program()
        inner_puzzle: Program = get_innerpuzzle_from_puzzle(puzzle)
        from_puzzle_hash: bytes32 = inner_puzzle.get_tree_hash()

        # we construct the actual transaction here

        key_value_pairs: Optional[list[tuple[str, Union[str, int]]]] = None
        if gateway_key_values:
            key_value_pairs = [(key, value) for (key, value) in gateway_key_values.items()]

        return await self._create_transaction(
            mode=mode,
            coins=coins,
            origin_coin=origin_coin,
            amount=amount,
            fee=fee,
            from_puzzle_hash=from_puzzle_hash,
            key_value_pairs=key_value_pairs,
            gateway_public_key=gateway_public_key,
            allow_missing_signature=(mode == GatewayMode.DETOKENIZATION),
            wallet_id=wallet_id,
        )

    async def send_tokenization_transaction(
        self,
        to_puzzle_hash: bytes32,
        amount: int,
        fee: int = 0,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        self.check_user(is_registry=True)
        await self.check_wallet(wallet_id=wallet_id, wallet_type=WalletType.STANDARD_WALLET)

        mode = GatewayMode.TOKENIZATION
        if self.mode_to_secret_key is None:
            raise ValueError("No secret keys provided for the registry!")
        if self.mode_to_public_key is None:
            raise ValueError("No public keys provided for the registry!")

        gateway_secret_key: PrivateKey = self.mode_to_secret_key[mode]
        gateway_public_key: G1Element = self.mode_to_public_key[mode]
        public_key_to_secret_key = {gateway_public_key: gateway_secret_key}

        coins: list[Coin] = await self.wallet_client.select_coins(
            amount=amount + fee,
            wallet_id=wallet_id,
            coin_selection_config=DEFAULT_TX_CONFIG.coin_selection_config,
        )
        if not len(coins):
            raise ValueError("Insufficient balance!")

        origin_coin: Coin = coins[0]

        logger.info(f"Creating transaction for mode {mode.name}:")
        logger.info(f"  - Recipient: {to_puzzle_hash.hex()}")
        logger.info(f"  - Amount: {amount}")
        logger.info(f"  - Fee: {fee}")

        result = await self._create_transaction(
            mode=mode,
            coins=coins,
            origin_coin=origin_coin,
            amount=amount,
            fee=fee,
            to_puzzle_hash=to_puzzle_hash,
            gateway_public_key=gateway_public_key,
            public_key_to_secret_key=public_key_to_secret_key,
            wallet_id=wallet_id,
        )
        transaction_records: list[TransactionRecord] = result["transaction_records"]

        await self.wallet_client.push_transactions(
            PushTransactions(transactions=transaction_records, sign=False), DEFAULT_TX_CONFIG
        )

        return result

    async def create_detokenization_request(
        self,
        amount: int,
        fee: int = 0,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        mode = GatewayMode.DETOKENIZATION
        if self.mode_to_public_key is None:
            raise ValueError("No public keys provided for the registry!")
        gateway_public_key: G1Element = self.mode_to_public_key[mode]

        result = await self._create_client_transaction(
            mode=mode,
            amount=amount,
            fee=fee,
            gateway_public_key=gateway_public_key,
            wallet_id=wallet_id,
        )
        transaction_records: list[TransactionRecord] = result["transaction_records"]
        spend_bundle: SpendBundle = result["spend_bundle"]
        content: str = bech32_encode("detok", convertbits(bytes(spend_bundle), 8, 5))

        transaction_records = [
            dataclasses.replace(transaction_record, spend_bundle=None) for transaction_record in transaction_records
        ]

        await self.wallet_client.push_transactions(
            PushTransactions(transactions=transaction_records, sign=False), DEFAULT_TX_CONFIG
        )

        result.update(
            {
                "transaction_records": transaction_records,
                "content": content,
            }
        )

        return result

    @classmethod
    async def parse_detokenization_request(
        cls,
        content: str,
    ) -> dict[str, Any]:
        (_, data) = bech32_decode(content, max_length=len(content))
        if data is None:
            raise ValueError("Invalid detokenization file!")

        data_bytes = bytes(convertbits(data, 5, 8, False))
        spend_bundle = SpendBundle.from_bytes(data_bytes)

        result: dict[str, Any] = {
            "spend_bundle": spend_bundle,
        }

        gateway_puzzle: Program = create_gateway_puzzle()

        coin_spend: CoinSpend
        gateway_coin_spend: Optional[CoinSpend] = None
        mode: Optional[GatewayMode] = None
        for coin_spend in spend_bundle.coin_spends:
            puzzle: Program = coin_spend.puzzle_reveal.to_program()
            solution: Program = coin_spend.solution.to_program()
            coin: Coin = coin_spend.coin

            puzzle_args: Optional[Iterator[Program]] = match_cat_puzzle(uncurry_puzzle(puzzle))

            # gateway spend is a CAT
            if puzzle_args is None:
                continue

            (_, asset_id_program, inner_puzzle) = puzzle_args
            asset_id = asset_id_program.as_atom()
            inner_solution = solution.at("f")

            # check for gateway puzzle
            if inner_puzzle != gateway_puzzle:
                continue

            inner_coin_spend = make_spend(
                coin=coin,
                puzzle_reveal=inner_puzzle,
                solution=inner_solution,
            )
            (mode, _) = parse_gateway_spend(coin_spend=inner_coin_spend, is_cat=False)
            gateway_coin_spend = coin_spend

            # only one gateway per SpendBundle
            break

        if gateway_coin_spend is None:
            return result

        origin_coin_id: bytes32 = gateway_coin_spend.coin.parent_coin_info

        inner_puzzle_hash: Optional[bytes32] = None
        for coin_spend in spend_bundle.coin_spends:
            coin = coin_spend.coin
            if coin.name() == origin_coin_id:
                puzzle = coin_spend.puzzle_reveal.to_program()
                puzzle_args = match_cat_puzzle(uncurry_puzzle(puzzle))
                if puzzle_args is None:
                    raise ValueError("Did not match CAT - invalid detokenization request")
                (_, _, inner_puzzle) = puzzle_args
                inner_puzzle_hash = inner_puzzle.get_tree_hash()

        assert inner_puzzle_hash is not None

        amount: int = gateway_coin_spend.coin.amount

        result.update(
            {
                "mode": mode,
                "from_puzzle_hash": inner_puzzle_hash,
                "amount": amount,
                "fee": estimate_fees(spend_bundle) - amount,
                "asset_id": asset_id,
                "gateway_coin_spend": coin_spend,
            }
        )
        return result

    async def sign_and_send_detokenization_request(
        self,
        content: str,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        self.check_user(is_registry=True)

        mode = GatewayMode.DETOKENIZATION
        if self.mode_to_secret_key is None:
            raise ValueError("No secret keys provided for the registry!")
        if self.mode_to_public_key is None:
            raise ValueError("No public keys provided for the registry!")
        gateway_secret_key: PrivateKey = self.mode_to_secret_key[mode]
        gateway_public_key: G1Element = self.mode_to_public_key[mode]
        public_key_to_secret_key = {gateway_public_key: gateway_secret_key}

        (_, data) = bech32_decode(content, max_length=len(content))
        if data is None:
            raise ValueError("Invalid detokenization file!")

        data_bytes = bytes(convertbits(data, 5, 8, False))
        unsigned_spend_bundle = SpendBundle.from_bytes(data_bytes)

        gateway_coin_spend: Optional[CoinSpend] = None
        signatures: list[G2Element] = []
        for coin_spend in unsigned_spend_bundle.coin_spends:
            signature = create_gateway_signature(
                coin_spend,
                agg_sig_additional_data=self.constants.AGG_SIG_ME_ADDITIONAL_DATA,
                public_key_to_secret_key=public_key_to_secret_key,
                allow_missing=True,
            )
            signatures.append(signature)

            if signature != G2Element():
                gateway_coin_spend = coin_spend

        aggregated_signature: G2Element = AugSchemeMPL.aggregate(signatures)
        if aggregated_signature == G2Element():
            raise ValueError("Invalid detokenization request!")

        spend_bundle = WalletSpendBundle.aggregate(
            [
                unsigned_spend_bundle,
                WalletSpendBundle(coin_spends=[], aggregated_signature=aggregated_signature),
            ]
        )
        if gateway_coin_spend is None:
            raise ValueError("Invalid detokenization request: Could not find gateway coin spend!")

        additions = spend_bundle.additions()
        transaction_record = TransactionRecord(
            confirmed_at_height=uint32(0),
            created_at_time=uint64(int(time.time())),
            to_puzzle_hash=gateway_coin_spend.coin.puzzle_hash,
            amount=uint64(gateway_coin_spend.coin.amount),
            fee_amount=uint64(estimate_fees(spend_bundle) - gateway_coin_spend.coin.amount),
            confirmed=False,
            sent=uint32(0),
            spend_bundle=spend_bundle,
            additions=additions,
            removals=[rem for rem in spend_bundle.removals() if rem not in additions],
            wallet_id=uint32(wallet_id),
            sent_to=[],
            trade_id=None,
            type=uint32(CLIMATE_WALLET_INDEX + mode.to_int()),
            name=spend_bundle.name(),
            memos=list(compute_memos(spend_bundle).items()),
            valid_times=ConditionValidTimes(),
        )
        transaction_records = [transaction_record]

        await self.wallet_client.push_transactions(
            PushTransactions(transactions=transaction_records, sign=False), DEFAULT_TX_CONFIG
        )

        return {
            "transaction_id": transaction_record.name,
            "transaction_records": transaction_records,
            "spend_bundle": spend_bundle,
        }

    async def send_permissionless_retirement_transaction(
        self,
        amount: int,
        beneficiary_name: bytes,
        beneficiary_address: bytes,
        fee: int = 0,
        beneficiary_puzzle_hash: Optional[bytes32] = None,
        wallet_id: int = 1,
    ) -> dict[str, Any]:
        mode = GatewayMode.PERMISSIONLESS_RETIREMENT

        if beneficiary_puzzle_hash is None:
            # no beneficiary supplied at all
            if beneficiary_address is None:
                beneficiary_puzzle_hash = await get_first_puzzle_hash(self.wallet_client)

        result = await self._create_client_transaction(
            mode=mode,
            amount=amount,
            fee=fee,
            wallet_id=wallet_id,
            gateway_key_values={
                "bn": beneficiary_name,
                "ba": beneficiary_address,
                "bp": beneficiary_puzzle_hash if beneficiary_puzzle_hash else b"",
            },
        )
        transaction_records: list[TransactionRecord] = result["transaction_records"]

        await self.wallet_client.push_transactions(
            PushTransactions(transactions=transaction_records, sign=False), DEFAULT_TX_CONFIG
        )

        return result


@dataclasses.dataclass
class ClimateObserverWallet(ClimateWalletBase):
    full_node_client: FullNodeRpcClient

    async def get_activities(
        self,
        mode: Optional[GatewayMode] = None,
        start_height: Optional[int] = None,
        end_height: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        modes: list[GatewayMode]
        if mode is None:
            modes = list(GatewayMode)
        else:
            modes = [mode]

        gateway_puzzle: Program = create_gateway_puzzle()
        gateway_cat_puzzle: Program = construct_cat_puzzle(
            mod_code=CAT_MOD,
            limitations_program_hash=self.tail_program_hash,
            inner_puzzle_or_hash=gateway_puzzle,
        )
        gateway_cat_puzzle_hash: bytes32 = gateway_cat_puzzle.get_tree_hash()

        coin_records: list[CoinRecord] = await self.full_node_client.get_coin_records_by_puzzle_hash(
            puzzle_hash=gateway_cat_puzzle_hash,
            start_height=start_height,
            end_height=end_height,
        )

        activities = []
        for coin_record in coin_records:
            coin: Coin = coin_record.coin
            height = coin_record.spent_block_index

            coin_spend = await self.full_node_client.get_puzzle_and_solution(
                coin_id=coin.name(),
                height=height,
            )

            if coin_spend is None:
                raise ValueError("No coin spend found!")
            (mode, tail_spend) = parse_gateway_spend(coin_spend=coin_spend, is_cat=True)

            if mode not in modes:
                continue

            tail_solution: Program = tail_spend.solution.to_program()
            delegated_solution: Program = tail_solution.at("r")
            key_value_pairs: Program = delegated_solution.at("f")

            metadata: dict[str, str] = {}
            for key_value_pair in key_value_pairs.as_iter():
                if (not key_value_pair.listp()) or (key_value_pair.at("r").listp()):
                    logger.warning(f"Coin {coin.name()} has incorrect metadata structure")
                    continue

                key_bytes = key_value_pair.at("f").as_atom()
                value_bytes = key_value_pair.at("r").as_atom()

                key = key_bytes.decode()
                if key in {"bp"}:
                    value = f"0x{value_bytes.hex()}"
                elif key in {"ba", "bn"}:
                    value = value_bytes.decode()
                else:
                    raise ValueError(f"Unknown key '{key}'!")

                metadata[key] = value

            activity = {
                "coin_record": coin_record,
                "coin_spend": coin_spend,
                "mode": mode,
                "metadata": metadata,
            }
            activities.append(activity)

        return activities
