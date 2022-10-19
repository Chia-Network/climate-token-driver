import dataclasses
from typing import Dict, List

import requests
from blspy import G1Element
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.types.blockchain_format.coin import Coin
from chia.types.coin_record import CoinRecord
from fastapi.encoders import jsonable_encoder

from app import schemas
from app.config import Settings
from app.core.climate_wallet.wallet import ClimateObserverWallet
from app.core.types import ClimateTokenIndex, GatewayMode
from app.errors import ErrorCode
from app.logger import logger

settings = Settings()
errorcode = ErrorCode()


@dataclasses.dataclass
class ClimateWareHouseCrud(object):
    url: str

    def get_climate_tokens(self) -> List[Dict]:
        try:
            r = requests.get(self.url + "/v1/units")
            if r.status_code != requests.codes.ok:
                raise errorcode.internal_server_error(
                    message="Call Climate API Failure"
                )

            return r.json()

        except TimeoutError as e:
            logger.error("Call Climate API Timeout, ErrorMessage: " + str(e))
            raise errorcode.internal_server_error("Call Climate API Timeout")


@dataclasses.dataclass
class BlockChainCrud(object):
    full_node_client: FullNodeRpcClient

    async def get_activities(
        self,
        org_uid: str,
        warehouse_project_id: str,
        vintage_year: int,
        sequence_num: int,
        public_key: G1Element,
        start_height: int,
        end_height: int,
        mode: GatewayMode,
    ) -> List[schemas.Activity]:

        token_index = ClimateTokenIndex(
            org_uid=org_uid,
            warehouse_project_id=warehouse_project_id,
            vintage_year=vintage_year,
            sequence_num=sequence_num,
        )
        wallet = ClimateObserverWallet(
            token_index=token_index,
            root_public_key=public_key,
            full_node_client=self.full_node_client,
        )
        activity_objs: List[Dict] = await wallet.get_activities(
            mode=mode,
            start_height=start_height,
            end_height=end_height,
        )

        activities: List[schemas.Activity] = []
        for obj in activity_objs:
            coin_record: CoinRecord = obj["coin_record"]
            metadata: Dict = jsonable_encoder(obj["metadata"])
            coin: Coin = coin_record.coin

            activity = schemas.Activity(
                org_uid=token_index.org_uid,
                warehouse_project_id=token_index.warehouse_project_id,
                vintage_year=token_index.vintage_year,
                sequence_num=token_index.sequence_num,
                asset_id=bytes(wallet.tail_program_hash),
                coin_id=coin_record.name,
                height=coin_record.spent_block_index,
                amount=coin.amount,
                mode=mode.name,
                metadata=metadata,
                timestamp=coin_record.timestamp,
            )
            activities.append(activity)

            logger.info(f"Found activity {jsonable_encoder(activity)}")

        return activities
