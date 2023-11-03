import dataclasses
from typing import Any, AnyStr, List, Optional, Tuple

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, desc, insert, or_, update
from sqlalchemy.orm import Session

from app import models, schemas
from app.db.base import Base
from app.errors import ErrorCode
from app.logger import logger

errorcode = ErrorCode()


@dataclasses.dataclass
class DBCrudBase(object):
    db: Session

    def create_object(self, model: Base) -> Base:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def batch_insert_ignore_db(self, table: AnyStr, models: List[Any]) -> bool:
        try:
            s = (
                insert(Base.metadata.tables[table])
                .prefix_with("OR IGNORE")
                .values(models)
            )
            self.db.execute(s)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Batch Insert DB Failure:{e}")
            raise errorcode.internal_server_error(message="Batch Insert DB Failure")

    def insert_db(self, models: Any) -> bool:
        try:
            self.db.add(models)
            self.db.commit()
            self.db.refresh(models)
            return True
        except Exception as e:
            logger.error(f"Insert DB Failure:{e}")
            raise errorcode.internal_server_error(message="Insert DB Failure")

    def update_db(self, table: Any, stmt: Any) -> bool:
        try:
            u = update(Base.metadata.tables[table]).values(stmt)
            self.db.execute(u)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Update DB Failure:{e}")
            raise errorcode.internal_server_error(message="Update DB Failure")

    def select_first_db(self, model: Any, order_by: Any) -> Any:
        try:
            return self.db.query(model).order_by(desc(order_by)).first()
        except Exception as e:
            logger.error(f"Select DB Failure:{e}")
            raise errorcode.internal_server_error(message="Select DB Failure")

    def select_activity_with_pagination(
        self, model: Any, filters: Any, order_by: Any, limit: int, page: int
    ) -> Tuple[Any, int]:
        try:
            query = self.db.query(model).filter(
                or_(*filters["or"]), and_(*filters["and"])
            )
            return (
                (
                    query.order_by(*order_by)
                    .limit(limit)
                    .offset((page - 1) * limit)
                    .all()
                ),
                query.count(),
            )
        except Exception as e:
            logger.error(f"Select DB Failure:{e}")
            raise errorcode.internal_server_error(message="Select DB Failure")


@dataclasses.dataclass
class DBCrud(DBCrudBase):
    def create_activity(self, activity: schemas.Activity) -> models.Activity:
        new_activity: models.Activity = self.create_object(
            models.Activity(**jsonable_encoder(activity))
        )
        return new_activity

    def batch_insert_ignore_activity(
        self,
        activities: List[schemas.Activity],
    ) -> bool:
        db_activities = []
        for activity in activities:
            db_activity = models.Activity(**jsonable_encoder(activity))
            db_activities.append(jsonable_encoder(db_activity))

        return self.batch_insert_ignore_db(
            table=models.Activity.__tablename__,
            models=db_activities,
        )

    def update_block_state(
        self,
        peak_height: Optional[int] = None,
        current_height: Optional[int] = None,
    ) -> bool:
        state = models.State()
        if peak_height is not None:
            state.peak_height = peak_height

        if current_height is not None:
            state.current_height = current_height

        return self.update_db(
            table=models.State.__tablename__,
            stmt=jsonable_encoder(state),
        )

    def select_block_state_first(self) -> models.State:
        selected_state: models.State = self.select_first_db(
            model=models.State,
            order_by=models.State.id,
        )
        return selected_state

    def select_activity_first(self) -> models.Activity:
        selected_activity: models.Activity = self.select_first_db(
            model=models.Activity,
            order_by=models.Activity.created_at,
        )
        return selected_activity
