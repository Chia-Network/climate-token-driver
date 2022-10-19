from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, func

from app.db.base import Base


class State(Base):
    __tablename__ = "state"

    id = Column(Integer, primary_key=True, index=True)
    current_height = Column(BigInteger)
    peak_height = Column(BigInteger)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=datetime.now)
