from sqlalchemy import create_engine, engine
from sqlalchemy.orm import Session, sessionmaker

from app import crud
from app.api import dependencies as deps
from app.config import settings


async def get_engine_cls() -> engine.Engine:
    async with deps.get_full_node_rpc_client() as full_node_client:
        blockchain_crud = crud.BlockChainCrud(full_node_client)
        challenge: str = await blockchain_crud.get_challenge()

    db_url: str = "sqlite:///" + str(settings.DB_PATH).replace("CHALLENGE", challenge)
    Engine: engine.Engine = create_engine(
        db_url, connect_args={"check_same_thread": False, "timeout": 15}
    )

    return Engine


async def get_session_local_cls() -> Session:
    Engine = await get_engine_cls()
    SessionLocal: Session = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

    return SessionLocal
