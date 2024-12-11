from __future__ import annotations

import asyncio
import json
import logging
from typing import List, Optional

from chia.consensus.block_record import BlockRecord
from chia.rpc.full_node_rpc_client import FullNodeRpcClient
from chia.util.byte_types import hexstr_to_bytes
from chia_rs import G1Element
from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi_utils.tasks import repeat_every
from sqlalchemy_utils import create_database, database_exists

from app import crud, schemas
from app.api import dependencies as deps
from app.config import ExecutionMode, settings
from app.db.base import Base
from app.db.session import get_engine_cls
from app.errors import ErrorCode
from app.models import State
from app.utils import disallow

router = APIRouter()
errorcode = ErrorCode()
lock = asyncio.Lock()
logger = logging.getLogger("ClimateToken")


@router.on_event("startup")
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])  # type: ignore[misc]
async def init_db() -> None:
    Engine = await get_engine_cls()

    if not database_exists(Engine.url):
        create_database(Engine.url)
        logger.info(f"Create database {Engine.url}")

    logger.info(f"Database {Engine.url} exists: " f"{database_exists(Engine.url)}")

    Base.metadata.create_all(Engine)

    async with deps.get_db_session_context() as db:
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

    start_height = state.current_height
    end_height = min(start_height + settings.BLOCK_RANGE, state.peak_height + 1)

    # make sure
    # - shallow records (<`MIN_DEPTH`) are revisited
    # - lookback 36 hours to compensate for CW metadata delay
    target_start_height = end_height - settings.MIN_DEPTH - settings.LOOKBACK_DEPTH

    if state.current_height == target_start_height:
        logger.info("Activity synced.")
        return False

    logger.info(f"Scanning blocks {start_height} - {end_height} for activity")

    # Check if SCAN_ALL_ORGANIZATIONS is defined and True, otherwise treat as False
    scan_all = getattr(settings, "SCAN_ALL_ORGANIZATIONS", False)

    all_organizations = climate_warehouse.get_climate_organizations()
    if not scan_all:
        # Convert to a list of organizations where `isHome` is True
        climate_organizations = [org for org in all_organizations.values() if org.get("isHome", False)]
    else:
        # Convert to a list of all organizations
        climate_organizations = list(all_organizations.values())

    for org in climate_organizations:
        org_uid = org["orgUid"]
        org_name = org["name"]

        org_metadata = climate_warehouse.get_climate_organizations_metadata(org_uid)
        if not org_metadata:
            logger.warning(f"Cannot get metadata in CADT organization: {org_name}")
            continue

        for key, value_str in org_metadata.items():
            try:
                tokenization_dict = json.loads(value_str)
                required_fields = [
                    "org_uid",
                    "warehouse_project_id",
                    "vintage_year",
                    "sequence_num",
                    "public_key",
                    "index",
                ]
                optional_fields = ["permissionless_retirement", "detokenization"]

                if not all(field in tokenization_dict for field in required_fields) or not any(
                    field in tokenization_dict for field in optional_fields
                ):
                    # not a tokenization record
                    continue

                public_key = G1Element.from_bytes(hexstr_to_bytes(tokenization_dict["public_key"]))
                activities: List[schemas.Activity] = await blockchain.get_activities(
                    org_uid=tokenization_dict["org_uid"],
                    warehouse_project_id=tokenization_dict["warehouse_project_id"],
                    vintage_year=tokenization_dict["vintage_year"],
                    sequence_num=tokenization_dict["sequence_num"],
                    public_key=public_key,
                    start_height=state.current_height,
                    end_height=end_height,
                    peak_height=state.peak_height,
                )

                if len(activities) == 0:
                    continue

                db_crud.batch_insert_ignore_activity(activities)
                logger.info(f"Activities for {org_name} and asset id: {key} added to the database.")

            # This is causing logging for benign errors, so commenting out for now
            # except json.JSONDecodeError as e:
            # logger.error(f"Failed to parse JSON for key {key} in organization {org_name}: {str(e)}")
            except Exception as e:
                logger.error(f"An error occurred for organization {org_name} under key {key}: {str(e)}")

    db_crud.update_block_state(current_height=target_start_height)
    return True


@router.on_event("startup")
@repeat_every(seconds=60, logger=logger)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])  # type: ignore[misc]
async def scan_token_activity() -> None:
    if lock.locked():
        return

    async with (
        lock,
        deps.get_db_session_context() as db,
        deps.get_full_node_rpc_client() as full_node_client,
    ):
        db_crud = crud.DBCrud(db=db)
        climate_warehouse = crud.ClimateWareHouseCrud(url=settings.CADT_API_SERVER_HOST, api_key=settings.CADT_API_KEY)
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
) -> None:
    state = await full_node_client.get_blockchain_state()
    peak_block_record: Optional[BlockRecord] = state["peak"]

    if peak_block_record is None:
        logger.warning("Full node is not synced")
        return

    db_crud.update_block_state(peak_height=peak_block_record.height)


@router.on_event("startup")
@repeat_every(seconds=10, logger=logger)
@disallow([ExecutionMode.REGISTRY, ExecutionMode.CLIENT])  # type: ignore[misc]
async def scan_blockchain_state() -> None:
    async with (
        deps.get_db_session_context() as db,
        deps.get_full_node_rpc_client() as full_node_client,
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
