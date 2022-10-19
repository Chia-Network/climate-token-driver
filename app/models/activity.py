from sqlalchemy import (
    JSON,
    BigInteger,
    Column,
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)

from app.db.base import Base


class Activity(Base):
    __tablename__ = "activity"

    id = Column(Integer, primary_key=True, index=True)

    org_uid = Column(String)
    warehouse_project_id = Column(String)
    vintage_year = Column(Integer)
    sequence_num = Column(Integer)
    asset_id = Column(String)

    coin_id = Column(String)
    height = Column(BigInteger)
    amount = Column(BigInteger)
    mode = Column(String)
    metadata_ = Column("metadata", JSON, default={})
    timestamp = Column(BigInteger)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "coin_id",
            name="uk_coin_id",
        ),
    )
