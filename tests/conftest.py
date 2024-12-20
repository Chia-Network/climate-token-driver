from __future__ import annotations

import pytest

# import all fixtures from chia-blockchain test suite
from chia._tests.conftest import *  # noqa: F403
from chia._tests.wallet.conftest import *  # noqa: F403
from chia._tests.wallet.rpc.test_wallet_rpc import *  # noqa: F403
from chia.clvm.spend_sim import sim_and_client
from fastapi.testclient import TestClient

from app.core.types import ClimateTokenIndex
from app.main import app


@pytest.fixture(scope="function")
async def sim_utils():
    async with sim_and_client(pass_prefarm=True) as (sim, client):
        yield sim, client


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
