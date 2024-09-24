from __future__ import annotations

import logging
import secrets
from typing import Dict, Tuple

import pytest
from chia.clvm.spend_sim import SimClient, SpendSim
from chia.types.blockchain_format.coin import Coin
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend, make_spend
from chia.types.mempool_inclusion_status import MempoolInclusionStatus
from chia.types.spend_bundle import SpendBundle
from chia.util.ints import uint64
from chia.wallet.cat_wallet.cat_utils import CAT_MOD, SpendableCAT, unsigned_spend_bundle_for_spendable_cats
from chia.wallet.lineage_proof import LineageProof
from chia.wallet.payment import Payment
from chia_rs import AugSchemeMPL, G1Element, G2Element, PrivateKey

from app.core.chialisp.gateway import create_gateway_puzzle
from app.core.chialisp.tail import create_tail_program
from app.core.climate_wallet.wallet_utils import create_gateway_request_and_spend, create_gateway_signature
from app.core.types import GatewayMode, TransactionRequest

logger = logging.getLogger(__name__)

ACS_MOD = Program.to(1)
ACS_MOD_HASH = ACS_MOD.get_tree_hash()
ZEROS = bytes32([0] * 32)


class TestCATLifecycle:
    @pytest.mark.anyio
    async def test_cat_lifecycle(
        self,
        sim_utils: Tuple[SpendSim, SimClient],
    ) -> None:
        """
        In this test, we perform the following spends:

            XCH
            └─ Gateway (Tokenization)
               └─ CAT
                  ├─ CAT
                  │  └─ Gateway (Detokenization)
                  │     └─ (No output coin)
                  └─ CAT
                     └─ Gateway (Retirement)
                        └─ (No output coin)
        """

        node, client = sim_utils

        root_secret_key: PrivateKey = AugSchemeMPL.key_gen(secrets.token_bytes(64))
        root_public_key: G1Element = root_secret_key.get_g1()
        mint_secret_key: PrivateKey = AugSchemeMPL.key_gen(secrets.token_bytes(64))
        mint_public_key: G1Element = mint_secret_key.get_g1()
        melt_secret_key: PrivateKey = AugSchemeMPL.key_gen(secrets.token_bytes(64))
        melt_public_key: G1Element = melt_secret_key.get_g1()

        public_key_to_secret_key: Dict[bytes, PrivateKey] = {
            root_public_key: root_secret_key,
            mint_public_key: mint_secret_key,
            melt_public_key: melt_secret_key,
        }

        tail_program: Program = create_tail_program(
            public_key=root_public_key,
            index=Program.to(["registry", "project", "vintage"]).get_tree_hash(),
        )
        tail_program_hash: bytes32 = tail_program.get_tree_hash()

        transaction_request: TransactionRequest
        unsigned_gateway_coin_spend: CoinSpend
        signature: G2Element

        # setup

        xch_puzzle: Program = ACS_MOD
        xch_puzzle_hash: bytes32 = xch_puzzle.get_tree_hash()

        await node.farm_block(xch_puzzle_hash)

        xch_coin: Coin = (await client.get_coin_records_by_puzzle_hash(xch_puzzle_hash))[0].coin

        # mint

        mode = GatewayMode.TOKENIZATION
        tokenize_amount: uint64 = uint64(100)
        tokenize_to_puzzle_hash: bytes32 = ACS_MOD_HASH

        # gateway mint spend

        (
            transaction_request,
            unsigned_gateway_coin_spend,
        ) = create_gateway_request_and_spend(
            origin_coin=xch_coin,
            mode=mode,
            tail_program=tail_program,
            amount=tokenize_amount,
            public_key=mint_public_key,
            to_puzzle_hash=tokenize_to_puzzle_hash,
        )
        signature = create_gateway_signature(
            unsigned_gateway_coin_spend,
            agg_sig_additional_data=node.defaults.AGG_SIG_ME_ADDITIONAL_DATA,
            public_key_to_secret_key=public_key_to_secret_key,
        )
        gateway_spend_bundle = SpendBundle(
            coin_spends=[unsigned_gateway_coin_spend],
            aggregated_signature=signature,
        )

        # xch spend

        xch_coin_spend = make_spend(
            coin=xch_coin,
            puzzle_reveal=xch_puzzle,
            solution=transaction_request.to_program(),
        )
        xch_spend_bundle = SpendBundle(
            coin_spends=[xch_coin_spend],
            aggregated_signature=G2Element(),
        )

        spend_bundle = SpendBundle.aggregate(
            [
                xch_spend_bundle,
                gateway_spend_bundle,
            ]
        )
        gateway_coin: Coin = unsigned_gateway_coin_spend.coin
        cat_coin: Coin = gateway_spend_bundle.additions().pop()

        result = await client.push_tx(spend_bundle)
        assert result == (MempoolInclusionStatus.SUCCESS, None)

        await node.farm_block()

        # split

        detokenize_amount: uint64 = uint64(10)
        retire_amount: uint64 = uint64(tokenize_amount - detokenize_amount)

        # cat spend

        transaction_request = TransactionRequest(
            payments=[
                Payment(puzzle_hash=ACS_MOD_HASH, amount=detokenize_amount, memos=[]),
                Payment(puzzle_hash=ACS_MOD_HASH, amount=retire_amount, memos=[]),
            ],
        )
        gateway_puzzle: Program = create_gateway_puzzle()
        gateway_puzzle_hash: bytes32 = gateway_puzzle.get_tree_hash()
        lineage_proof = LineageProof(
            parent_name=gateway_coin.parent_coin_info,
            inner_puzzle_hash=gateway_puzzle_hash,
            amount=uint64(gateway_coin.amount),
        )
        spendable_cat = SpendableCAT(
            coin=cat_coin,
            limitations_program_hash=tail_program_hash,
            lineage_proof=lineage_proof,
            extra_delta=0,
            inner_puzzle=ACS_MOD,
            inner_solution=transaction_request.to_program(),
        )
        spend_bundle = unsigned_spend_bundle_for_spendable_cats(CAT_MOD, [spendable_cat])

        (
            cat_coin_for_detokenization,
            cat_coin_for_retirement,
        ) = spend_bundle.additions()

        result = await client.push_tx(spend_bundle)
        assert result == (MempoolInclusionStatus.SUCCESS, None)

        await node.farm_block()

        # detokenize

        mode = GatewayMode.DETOKENIZATION

        # gateway melt spend

        (
            transaction_request,
            unsigned_gateway_coin_spend,
        ) = create_gateway_request_and_spend(
            origin_coin=cat_coin_for_detokenization,
            mode=mode,
            tail_program=tail_program,
            amount=detokenize_amount,
            public_key=melt_public_key,
            from_puzzle_hash=ACS_MOD_HASH,
        )
        signature = create_gateway_signature(
            unsigned_gateway_coin_spend,
            agg_sig_additional_data=node.defaults.AGG_SIG_ME_ADDITIONAL_DATA,
            public_key_to_secret_key=public_key_to_secret_key,
        )
        gateway_spend_bundle = SpendBundle(
            coin_spends=[unsigned_gateway_coin_spend],
            aggregated_signature=signature,
        )

        # cat spend

        lineage_proof = LineageProof(
            parent_name=cat_coin.parent_coin_info,
            inner_puzzle_hash=ACS_MOD_HASH,
            amount=uint64(cat_coin.amount),
        )
        spendable_cat = SpendableCAT(
            coin=cat_coin_for_detokenization,
            limitations_program_hash=tail_program_hash,
            lineage_proof=lineage_proof,
            extra_delta=0,
            inner_puzzle=ACS_MOD,
            inner_solution=transaction_request.to_program(),
        )
        cat_spend_bundle = unsigned_spend_bundle_for_spendable_cats(CAT_MOD, [spendable_cat])

        spend_bundle = SpendBundle.aggregate(
            [
                cat_spend_bundle,
                gateway_spend_bundle,
            ]
        )

        result = await client.push_tx(spend_bundle)
        assert result == (MempoolInclusionStatus.SUCCESS, None)

        await node.farm_block()

        # retire

        mode = GatewayMode.PERMISSIONLESS_RETIREMENT

        # gateway melt spend

        (
            transaction_request,
            unsigned_gateway_coin_spend,
        ) = create_gateway_request_and_spend(
            origin_coin=cat_coin_for_retirement,
            mode=mode,
            tail_program=tail_program,
            amount=retire_amount,
            from_puzzle_hash=ACS_MOD_HASH,
            key_value_pairs=[(b"b", ZEROS)],
        )
        signature = create_gateway_signature(
            unsigned_gateway_coin_spend,
            agg_sig_additional_data=node.defaults.AGG_SIG_ME_ADDITIONAL_DATA,
            public_key_to_secret_key=public_key_to_secret_key,
        )
        gateway_spend_bundle = SpendBundle(
            coin_spends=[unsigned_gateway_coin_spend],
            aggregated_signature=signature,
        )

        # cat spend

        lineage_proof = LineageProof(
            parent_name=cat_coin.parent_coin_info,
            inner_puzzle_hash=ACS_MOD_HASH,
            amount=uint64(cat_coin.amount),
        )
        spendable_cat = SpendableCAT(
            coin=cat_coin_for_retirement,
            limitations_program_hash=tail_program_hash,
            lineage_proof=lineage_proof,
            extra_delta=0,
            inner_puzzle=ACS_MOD,
            inner_solution=transaction_request.to_program(),
        )
        cat_spend_bundle = unsigned_spend_bundle_for_spendable_cats(CAT_MOD, [spendable_cat])

        spend_bundle = SpendBundle.aggregate(
            [
                cat_spend_bundle,
                gateway_spend_bundle,
            ]
        )

        result = await client.push_tx(spend_bundle)
        assert result == (MempoolInclusionStatus.SUCCESS, None)

        await node.farm_block()
