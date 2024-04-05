from __future__ import annotations

import pytest
import pytest_asyncio
from chia.clvm.spend_sim import SimClient, SpendSim
from fastapi.testclient import TestClient

from app.core.types import ClimateTokenIndex
from app.main import app

# import all fixtures from chia-blockchain test suite
from tests.conftest import *  # noqa


@pytest_asyncio.fixture(scope="function")
async def sim_full_node():
    async with SpendSim.managed() as sim_full_node:
        await sim_full_node.farm_block()
        yield sim_full_node


@pytest_asyncio.fixture(scope="function")
async def sim_full_node_client(sim_full_node):
    return SimClient(sim_full_node)


@pytest.fixture(scope="function")
def token_index() -> ClimateTokenIndex:
    return ClimateTokenIndex(
        org_uid="ORG_UID",
        warehouse_project_id="WAREHOUSE_PROJECT_ID",
        vintage_year=2050,
    )


@pytest.fixture(scope="function")
def fastapi_client() -> TestClient:
    return TestClient(app)
