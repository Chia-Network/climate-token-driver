import asyncio
from typing import Dict, List

from blspy import G1Element
from chia.consensus.block_record import BlockRecord
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.util.byte_types import hexstr_to_bytes
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
from sqlalchemy_utils import create_database, database_exists

from app import crud, schemas
from app.api import dependencies as deps
from app.config import ExecutionMode, Settings
from app.db.base import Base
from app.db.session import Engine
from app.errors import ErrorCode
from app.logger import logger
from app.models import State
from app.utils import as_async_contextmanager, disallow

router = APIRouter()
settings = Settings()
errorcode = ErrorCode()
lock = asyncio.Lock()


@router.on_event("startup")
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def init_db():
    if not database_exists(Engine.url):
        create_database(Engine.url)
        logger.info(f"Create database {Engine.url}")

    logger.info(f"Database {Engine.url} exists: " f"{database_exists(Engine.url)}")

    Base.metadata.create_all(Engine)

    async with as_async_contextmanager(deps.get_db_session) as db:
        state = State(id=1, current_height=settings.BLOCK_START, peak_height=None)
        db_state = [jsonable_encoder(state)]

        db_crud = crud.DBCrud(db=db)
        db_crud.batch_insert_ignore_db(table=State.__tablename__, models=db_state)


async def _scan_token_activity(
    db_crud: crud.DBCrud,
    climate_warehouse: crud.ClimateWareHouseCrud,
    blockchain: crud.BlockChainCrud,
) -> bool:
    state = db_crud.select_block_state_first()
    if state.peak_height is None:
        logger.warning("Full node state has not been retrieved.")
        return False

    if state.current_height == state.peak_height:
        logger.info("Activity synced.")
        return False

    start_height = state.current_height + 1
    end_height = min(start_height + settings.BLOCK_RANGE - 1, state.peak_height)

    logger.info(f"Scanning blocks {start_height} - {end_height} for activity")

    climate_tokens = climate_warehouse.combine_climate_units_and_metadata(search={})
    for token in climate_tokens:

        if token["token"].get("public_key", "") == "":
            continue

        public_key = G1Element.from_bytes(hexstr_to_bytes(token["token"]["public_key"]))

        activities: List[schemas.Activity] = await blockchain.get_activities(
            org_uid=token["orgUid"],
            warehouse_project_id=token["issuance"]["warehouseProjectId"],
            vintage_year=token["vintageYear"],
            sequence_num=token["token"]["sequence_num"],
            public_key=public_key,
            start_height=start_height,
            end_height=end_height,
            peak_height=state.peak_height,
        )

        if len(activities) == 0:
            continue

        db_crud.batch_insert_ignore_activity(activities)

    db_crud.update_block_state(current_height=end_height)
    return True


@router.on_event("startup")
@repeat_every(seconds=60, logger=logger)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def scan_token_activity() -> None:
    if lock.locked():
        return

    async with (
        lock,
        as_async_contextmanager(deps.get_db_session) as db,
        as_async_contextmanager(deps.get_full_node_rpc_client) as full_node_client,
    ):

        db_crud = crud.DBCrud(db=db)
        climate_warehouse = crud.ClimateWareHouseCrud(url=settings.CLIMATE_API_URL)
        blockchain = crud.BlockChainCrud(full_node_client=full_node_client)

        try:
            while await _scan_token_activity(
                db_crud=db_crud,
                climate_warehouse=climate_warehouse,
                blockchain=blockchain,
            ):
                pass

        except TimeoutError as e:
            logger.error("Call API Time Out, ErrorMessage: " + str(e))
            raise errorcode.internal_server_error(message="Call API Time Out")

        except HTTPException as e:
            logger.error("Insert DB Failure, ErrorMessage: " + str(e))
            raise errorcode.internal_server_error(message="Insert DB Failure")

        except Exception as e:
            logger.error("Get Retire Token Failure, ErrorMessage: " + str(e))
            raise errorcode.internal_server_error(message="Get Retire Token Failure")


async def _scan_blockchain_state(
    db_crud: crud.DBCrud,
    full_node_client: FullNodeRpcClient,
):
    state: Dict = await full_node_client.get_blockchain_state()
    peak: Dict = state.get("peak")

    if peak is None:
        logger.warning("Full node is not synced")
        return

    peak_block_record = BlockRecord.from_json_dict(peak)
    db_crud.update_block_state(peak_height=peak_block_record.height)


@router.on_event("startup")
@repeat_every(seconds=10, logger=logger)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])
async def scan_blockchain_state() -> None:
    async with (
        as_async_contextmanager(deps.get_db_session) as db,
        as_async_contextmanager(deps.get_full_node_rpc_client) as full_node_client,
    ):

        db_crud = crud.DBCrud(db=db)

        try:
            await _scan_blockchain_state(
                db_crud=db_crud,
                full_node_client=full_node_client,
            )

        except HTTPException as e:
            logger.error("Update DB Failure, ErrorMessage: " + str(e))
            raise errorcode.internal_server_error(message="Update DB Failure")
