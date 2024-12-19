from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import activities, cron, keys, organizations, tokens, transactions

router = APIRouter(
    prefix="/v1",
    tags=["v1"],
)


@router.get("/info")
async def get_info() -> dict[str, str]:
    return {
        "blockchain_name": "Chia Network",
        "blockchain_name_short": "chia",
    }


router.include_router(cron.router)
router.include_router(
    tokens.router,
    prefix="/tokens",
    tags=["tokens"],
)
router.include_router(
    transactions.router,
    prefix="/transactions",
    tags=["transactions"],
)
router.include_router(
    activities.router,
    prefix="/activities",
    tags=["activities"],
)
router.include_router(
    keys.router,
    prefix="/keys",
    tags=["keys"],
)
router.include_router(
    organizations.router,
    prefix="/organizations",
    tags=["organizations"],
)
