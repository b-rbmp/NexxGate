import decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, tuple_
from sqlalchemy import func, distinct
from datetime import datetime


from app import models, schemas
from app.db.db import engine


class CRUDAccessLog:

    @staticmethod
    def create(db: Session, item: schemas.AccessLogCreateOut):

        db_item = models.AccessLog()
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def get_list(
        db: Session,
        skip: int | None,
        limit: int | None,
        device_node_id: int | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        uid: str | None = None,
        granted: bool | None = None,
    ) -> Dict[List[models.AccessLog], int]:

        response_get = {"elements": List[models.AccessLog], "count-total": int}

        query_result = db.query(models.AccessLog)

        # Filters
        if device_node_id is not None:
            query_result = query_result.filter(
                models.AccessLog.device_node_id == device_node_id
            )

        if start_date:
            query_result = query_result.filter(models.AccessLog.timestamp >= start_date)

        if end_date:
            query_result = query_result.filter(models.AccessLog.timestamp <= end_date)

        if uid is not None:
            query_result = query_result.filter(models.AccessLog.uid == uid)

        if granted is not None:
            query_result = query_result.filter(models.AccessLog.granted == granted)

        response_get["total-count"] = str(query_result.count())

        query_result = query_result.order_by(models.AccessLog.timestamp.desc())

        if skip is not None and limit is not None:
            query_result = query_result.offset(skip).limit(limit)

        response_get["elements"] = query_result.all()

        return response_get

    @staticmethod
    def update(db: Session, item: schemas.AccessLogUpdateIn, db_item: models.AccessLog):
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.AccessLog) -> bool:
        db.delete(db_item)
        db.commit()
        return True

    @staticmethod
    def count_all(db: Session) -> int:
        return db.query(
            distinct(
                tuple_(models.AccessLog.device_node_id, models.AccessLog.timestamp)
            )
        ).count()

    @staticmethod
    def get_last_record(db: Session) -> models.AccessLog:

        return (
            db.query(models.AccessLog)
            .order_by(models.AccessLog.timestamp.desc())
            .first()
        )


class CRUDDevice:

    @staticmethod
    def get_by_node_id(db: Session, node_id: str) -> models.Device:
        return db.query(models.Device).filter(models.Device.node_id == node_id).first()

    @staticmethod
    def get_by_api_key(db: Session, api_key: str) -> models.Device:
        return db.query(models.Device).filter(models.Device.api_key == api_key).first()

    @staticmethod
    def create(db: Session, item: schemas.DeviceCreateOut):

        db_item = models.Device()
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def get_list(
        db: Session,
        skip: int | None,
        limit: int | None,
        node_id: str | None = None,
        api_key: str | None = None,
        edge_server_id: int | None = None,
    ) -> Dict[List[models.Device], int]:

        response_get = {"elements": List[models.Device], "count-total": int}

        query_result = db.query(models.Device)

        # Filters
        if node_id is not None:
            query_result = query_result.filter(models.Device.node_id == node_id)

        if api_key is not None:
            query_result = query_result.filter(models.Device.api_key == api_key)

        if edge_server_id is not None:
            query_result = query_result.filter(
                models.Device.edge_server_id == edge_server_id
            )

        response_get["total-count"] = str(query_result.count())

        query_result = query_result.order_by(models.Device.node_id.desc())

        if skip is not None and limit is not None:
            query_result = query_result.offset(skip).limit(limit)

        response_get["elements"] = query_result.all()

        return response_get

    @staticmethod
    def update(db: Session, item: schemas.DeviceUpdateIn, db_item: models.Device):
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.Device) -> bool:
        db.delete(db_item)
        db.commit()
        return True

    @staticmethod
    def count_all(db: Session) -> int:
        return db.query(models.Device).count()


class EdgeServer:

    @staticmethod
    def get_by_id(db: Session, id: int) -> models.EdgeServer:
        return db.query(models.EdgeServer).filter(models.EdgeServer.id == id).first()

    @staticmethod
    def get_by_api_key(db: Session, api_key: str) -> models.EdgeServer:
        return (
            db.query(models.EdgeServer)
            .filter(models.EdgeServer.api_key == api_key)
            .first()
        )

    @staticmethod
    def create(db: Session, item: schemas.EdgeServerCreateOut):

        db_item = models.EdgeServer()
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def get_list(
        db: Session,
        skip: int | None,
        limit: int | None,
        api_key: str | None = None,
        name: str | None = None,
        city: str | None = None,
        country: str | None = None,
        latitude: decimal.Decimal | None = None,
        longitude: decimal.Decimal | None = None,
        altitude: decimal.Decimal | None = None,
    ) -> Dict[List[models.EdgeServer], int]:

        response_get = {"elements": List[models.EdgeServer], "count-total": int}

        query_result = db.query(models.EdgeServer)

        # Filters
        if api_key is not None:
            query_result = query_result.filter(models.EdgeServer.api_key == api_key)

        if name is not None:
            query_result = query_result.filter(models.EdgeServer.name == name)

        if city is not None:
            query_result = query_result.filter(models.EdgeServer.city == city)

        if country is not None:
            query_result = query_result.filter(models.EdgeServer.country == country)

        if latitude is not None:
            query_result = query_result.filter(models.EdgeServer.latitude == latitude)

        if longitude is not None:
            query_result = query_result.filter(models.EdgeServer.longitude == longitude)

        if altitude is not None:
            query_result = query_result.filter(models.EdgeServer.altitude == altitude)

        response_get["total-count"] = str(query_result.count())

        query_result = query_result.order_by(models.EdgeServer.id.desc())

        if skip is not None and limit is not None:
            query_result = query_result.offset(skip).limit(limit)

        response_get["elements"] = query_result.all()

        return response_get

    @staticmethod
    def update(
        db: Session, item: schemas.EdgeServerUpdateIn, db_item: models.EdgeServer
    ):
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.EdgeServer) -> bool:
        db.delete(db_item)
        db.commit()
        return True


class CRUDUserAuth:
    @staticmethod
    def get_by_uid(db: Session, uid: str) -> models.UserAuth:
        return db.query(models.UserAuth).filter(models.UserAuth.uid == uid).first()

    @staticmethod
    def get_by_id(db: Session, id: int) -> models.UserAuth:
        return db.query(models.UserAuth).filter(models.UserAuth.id == id).first()

    @staticmethod
    def create(db: Session, item: schemas.UserAuthCreateOut):

        db_item = models.UserAuth()
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def get_list(
        db: Session,
        skip: int | None,
        limit: int | None,
        uid: str | None = None,
        last_access: datetime | None = None,
        last_device_node_id: int | None = None,
        name: str | None = None,
        email: str | None = None,
        authenticated: bool | None = None,
    ) -> Dict[List[models.UserAuth], int]:

        response_get = {"elements": List[models.UserAuth], "count-total": int}

        query_result = db.query(models.UserAuth)

        # Filters
        if uid is not None:
            query_result = query_result.filter(models.UserAuth.uid == uid)

        if last_access is not None:
            query_result = query_result.filter(
                models.UserAuth.last_access == last_access
            )

        if last_device_node_id is not None:
            query_result = query_result.filter(
                models.UserAuth.last_device_node_id == last_device_node_id
            )

        if name is not None:
            query_result = query_result.filter(models.UserAuth.name == name)

        if email is not None:
            query_result = query_result.filter(models.UserAuth.email == email)

        if authenticated is not None:
            query_result = query_result.filter(
                models.UserAuth.authenticated == authenticated
            )

        response_get["total-count"] = str(query_result.count())

        query_result = query_result.order_by(models.UserAuth.id.desc())

        if skip is not None and limit is not None:
            query_result = query_result.offset(skip).limit(limit)

        response_get["elements"] = query_result.all()

        return response_get

    @staticmethod
    def update(db: Session, item: schemas.UserAuthUpdateIn, db_item: models.UserAuth):
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.UserAuth) -> bool:
        db.delete(db_item)
        db.commit()
        return True


crud_access_log = CRUDAccessLog()
crud_device = CRUDDevice()
crud_edge_server = EdgeServer()
crud_auth_user = CRUDUserAuth()
