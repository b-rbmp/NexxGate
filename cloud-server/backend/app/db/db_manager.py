import decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, tuple_
from sqlalchemy import func, distinct
from datetime import datetime


from app import models, schemas
from app.db.db import engine

class CRUDAccessLog:
    """
    This class provides CRUD operations for the AccessLog model.
    """

    @staticmethod
    def create(db: Session, item: schemas.AccessLogCreateOut):
        """
        Create a new AccessLog record in the database.

        Args:
            db (Session): The database session.
            item (schemas.AccessLogCreateOut): The AccessLog data to be created.

        Returns:
            models.AccessLog: The created AccessLog record.
        """
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
        """
        Get a list of AccessLog records from the database based on the provided filters.

        Args:
            db (Session): The database session.
            skip (int | None): The number of records to skip.
            limit (int | None): The maximum number of records to retrieve.
            device_node_id (int | None): The device node ID to filter by.
            start_date (datetime | None): The start date to filter by.
            end_date (datetime | None): The end date to filter by.
            uid (str | None): The UID to filter by.
            granted (bool | None): The granted status to filter by.

        Returns:
            Dict[List[models.AccessLog], int]: A dictionary containing the list of AccessLog records and the total count.
        """

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
        """
        Update an existing AccessLog record in the database.

        Args:
            db (Session): The database session.
            item (schemas.AccessLogUpdateIn): The updated AccessLog data.
            db_item (models.AccessLog): The AccessLog record to be updated.

        Returns:
            models.AccessLog: The updated AccessLog record.
        """

        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.AccessLog) -> bool:
        """
        Delete an existing AccessLog record from the database.

        Args:
            db (Session): The database session.
            db_item (models.AccessLog): The AccessLog record to be deleted.

        Returns:
            bool: True if the deletion is successful, False otherwise.
        """
        db.delete(db_item)
        db.commit()
        return True

    @staticmethod
    def count_all(db: Session) -> int:
        """
        Count the total number of unique AccessLog records in the database.

        Args:
            db (Session): The database session.

        Returns:
            int: The total count of unique AccessLog records.
        """
        return db.query(
            distinct(
                tuple_(models.AccessLog.device_node_id, models.AccessLog.timestamp)
            )
        ).count()

    @staticmethod
    def get_last_record(db: Session) -> models.AccessLog:
        """
        Get the last recorded AccessLog from the database.

        Args:
            db (Session): The database session.

        Returns:
            models.AccessLog: The last recorded AccessLog.
        """
        return (
            db.query(models.AccessLog)
            .order_by(models.AccessLog.timestamp.desc())
            .first()
        )


class CRUDDevice:
    """
    This class provides CRUD operations for the Device model.
    """

    @staticmethod
    def get_by_node_id(db: Session, node_id: str) -> models.Device:
        """
        Get a Device record from the database based on the provided node ID.

        Args:
            db (Session): The database session.
            node_id (str): The node ID to filter by.

        Returns:
            models.Device: The Device record.
        """
        return db.query(models.Device).filter(models.Device.node_id == node_id).first()

    @staticmethod
    def get_by_api_key(db: Session, api_key: str) -> models.Device:
        """
        Get a Device record from the database based on the provided API key.

        Args:
            db (Session): The database session.
            api_key (str): The API key to filter by.
        
        Returns:
            models.Device: The Device record.
        """
        return db.query(models.Device).filter(models.Device.api_key == api_key).first()

    @staticmethod
    def create(db: Session, item: schemas.DeviceCreateOut):
        """
        Create a new Device record in the database.

        Args:
            db (Session): The database session.
            item (schemas.DeviceCreateOut): The Device data to be created.

        Returns:
            models.Device: The created Device record.
        """
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
        """
        Get a list of Device records from the database based on the provided filters.

        Args:
            db (Session): The database session.
            skip (int | None): The number of records to skip.
            limit (int | None): The maximum number of records to retrieve.
            node_id (str | None): The node ID to filter by.
            api_key (str | None): The API key to filter by.
            edge_server_id (int | None): The edge server ID to filter by.
        
        Returns:
            Dict[List[models.Device], int]: A dictionary containing the list of Device records and the total count.
        """
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
        """
        Update an existing Device record in the database.

        Args:
            db (Session): The database session.
            item (schemas.DeviceUpdateIn): The updated Device data.
            db_item (models.Device): The Device record to be updated.

        Returns:
            models.Device: The updated Device record.
        """

        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.Device) -> bool:
        """
        Delete an existing Device record from the database.

        Args:
            db (Session): The database session.
            db_item (models.Device): The Device record to be deleted.
        """
        db.delete(db_item)
        db.commit()
        return True

    @staticmethod
    def count_all(db: Session) -> int:
        """
        Count the total number of unique Device records in the database.

        Args:
            db (Session): The database session.
        """
        return db.query(models.Device).count()


class EdgeServer:
    """
    This class provides CRUD operations for the EdgeServer model.
    """

    @staticmethod
    def get_by_id(db: Session, id: int) -> models.EdgeServer:
        """
        Get an EdgeServer record from the database based on the provided ID.

        Args:
            db (Session): The database session.
            id (int): The ID to filter by.
        """
        return db.query(models.EdgeServer).filter(models.EdgeServer.id == id).first()

    @staticmethod
    def get_by_api_key(db: Session, api_key: str) -> models.EdgeServer:
        """
        Get an EdgeServer record from the database based on the provided API key.

        Args:
            db (Session): The database session.
            api_key (str): The API key to filter by.
        """
        return (
            db.query(models.EdgeServer)
            .filter(models.EdgeServer.api_key == api_key)
            .first()
        )

    @staticmethod
    def create(db: Session, item: schemas.EdgeServerCreateOut):
        """
        Create a new EdgeServer record in the database.

        Args:
            db (Session): The database session.
            item (schemas.EdgeServerCreateOut): The EdgeServer data to be created.

        Returns:
            models.EdgeServer: The created EdgeServer record.
        """
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
        """
        Get a list of EdgeServer records from the database based on the provided filters.

        Args:
            db (Session): The database session.
            skip (int | None): The number of records to skip.
            limit (int | None): The maximum number of records to retrieve.
            api_key (str | None): The API key to filter by.
            name (str | None): The name to filter by.
            city (str | None): The city to filter by.
            country (str | None): The country to filter by.
            latitude (decimal.Decimal | None): The latitude to filter by.
            longitude (decimal.Decimal | None): The longitude to filter by.
            altitude (decimal.Decimal | None): The altitude to filter by.
        
        Returns:
            Dict[List[models.EdgeServer], int]: A dictionary containing the list of EdgeServer records and the total count.
        """

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
        """
        Update an existing EdgeServer record in the database.

        Args:
            db (Session): The database session.
            item (schemas.EdgeServerUpdateIn): The updated EdgeServer data.
            db_item (models.EdgeServer): The EdgeServer record to be updated.
        
        Returns:
            models.EdgeServer: The updated EdgeServer record.
        """
        # Update model class variable from requested fields
        for var, value in vars(item).items():
            setattr(db_item, var, value) if value is not None else None

        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, db_item: models.EdgeServer) -> bool:
        """
        Delete an existing EdgeServer record from the database.

        Args:
            db (Session): The database session.
            db_item (models.EdgeServer): The EdgeServer record to be deleted.

        Returns:
            bool: True if the deletion is successful, False otherwise.
        """

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
