from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import crud
from app.config import settings

if not settings.DB_PATH.exists():
    settings.DB_PATH.mkdir()

orgs = crud.ClimateWareHouseCrud(url=settings.CLIMATE_API_URL).get_climate_organizations()

for org in orgs.values():
    if org["isHome"]:
        settings.DB_URL = settings.DB_URL + org["orgUid"] + ".sqlite"

Engine = create_engine(settings.DB_URL, connect_args={"check_same_thread": False, "timeout": 15})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)
