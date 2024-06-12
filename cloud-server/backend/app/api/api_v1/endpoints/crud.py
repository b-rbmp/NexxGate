from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app import schemas

from app.dependencies import get_db
from app.db.db_manager import crud_device

# Create the API Router
router = APIRouter()


@router.get("/devices/", tags=["devices"], response_model=List[schemas.DeviceInDBBase])
def get_devices(
    response: Response,
    skip: int | None = Query(None, ge=0, description="Offset"),
    limit: int | None = Query(None, le=1000, description="Limit"),
    node_id: str | None = Query(None, description="Node ID"),
    api_key: str | None = Query(None, description="API key"),
    edge_server_id: int | None = Query(None, description="Edge Server ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve a list of devices based on the provided filters.

    Parameters:
    - response: The response object.
    - skip: The offset value for pagination (default: None).
    - limit: The limit value for pagination (default: None).
    - node_id: The ID of the node to filter devices (default: None).
    - api_key: The API key to filter devices (default: None).
    - edge_server_id: The ID of the edge server to filter devices (default: None).
    - db: The database session dependency.

    Returns:
    - A list of devices matching the provided filters.
    """
    devices = crud_device.get_list(
        db=db,
        skip=skip,
        limit=limit,
        node_id=node_id,
        api_key=api_key,
        edge_server_id=edge_server_id,
    )

    response.headers["X-Total-Count"] = devices["total-count"]

    return devices["elements"]


@router.post("/devices/", tags=["devices"], response_model=schemas.DeviceInDBBase)
def create_device(
    device: schemas.DeviceCreateIn,
    db: Session = Depends(get_db),
):
    """
    Create a new device.

    Args:
        device (schemas.DeviceCreateIn): The device information to be created.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Raises:
        HTTPException: If a device with the same node_id or api_key already exists.

    Returns:
        schemas.DeviceInDBBase: The created device information.
    """
    db_device = crud_device.get_by_node_id(db=db, node_id=device.node_id)
    if db_device is not None:
        raise HTTPException(
            status_code=409, detail="Device with the same node_id already registered"
        )

    db_device = crud_device.get_by_api_key(db=db, api_key=device.api_key)
    if db_device is not None:
        raise HTTPException(
            status_code=409, detail="Device with the same api_key already registered"
        )

    device_out = schemas.DeviceCreateOut(**device.model_dump())
    return crud_device.create(db=db, item=device_out)


@router.get(
    "/devices/{node_id}", tags=["devices"], response_model=schemas.DeviceInDBBase
)
def get_device_by_node_id(
    node_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a device by its node ID.

    Args:
        node_id (int): The node ID of the device to retrieve.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.DeviceInDBBase: The device information.

    Raises:
        HTTPException: If the node ID is not found in the database.
    """
    db_device = crud_device.get_by_node_id(db=db, node_id=node_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Node ID not found")
    return db_device


@router.put(
    "/devices/{node_id}", tags=["devices"], response_model=schemas.DeviceInDBBase
)
def update_device(
    node_id: int,
    device: schemas.DeviceUpdateIn,
    db: Session = Depends(get_db),
):
    """
    Update a device with the specified node ID.

    Args:
        node_id (int): The ID of the device to update.
        device (schemas.DeviceUpdateIn): The updated device information.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.DeviceInDBBase: The updated device information.

    Raises:
        HTTPException: If the specified node ID is not found in the database.
    """
    db_device = crud_device.get_by_node_id(db=db, node_id=node_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Node ID not found")

    device_out = schemas.DeviceUpdateOut(**device.model_dump())
    return crud_device.update(db=db, item=device_out, db_item=db_device)


@router.delete("/devices/{node_id}", tags=["devices"], response_model=bool)
def delete(
    node_id: int,
    db: Session = Depends(get_db),
):
    """
    Delete a device by its node ID.

    Args:
        node_id (int): The node ID of the device to be deleted.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        bool: True if the device is successfully deleted, False otherwise.

    Raises:
        HTTPException: If the node ID is not found in the database.
    """
    db_device = crud_device.get_by_node_id(db=db, node_id=node_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Node ID not found")
    return crud_device.delete(db=db, db_item=db_device)


# Edge Server
from app.db.db_manager import crud_edge_server


@router.get(
    "/edge_servers/",
    tags=["edge_servers"],
    response_model=List[schemas.EdgeServerInDBBase],
)
def get_edge_servers(
    response: Response,
    skip: int | None = Query(None, ge=0, description="Offset"),
    limit: int | None = Query(None, le=1000, description="Limit"),
    api_key: str | None = Query(None, description="API key"),
    name: str | None = Query(None, description="Name"),
    city: str | None = Query(None, description="City"),
    country: str | None = Query(None, description="Country"),
    db: Session = Depends(get_db),
):
    """
    Retrieve a list of edge servers based on the provided filters.

    Parameters:
    - response: The response object.
    - skip: The offset value for pagination (default: None).
    - limit: The limit value for pagination (default: None).
    - api_key: The API key for authentication (default: None).
    - name: The name of the edge server (default: None).
    - city: The city where the edge server is located (default: None).
    - country: The country where the edge server is located (default: None).
    - db: The database session.

    Returns:
    - A list of edge servers matching the provided filters.
    """
    edge_servers = crud_edge_server.get_list(
        db=db,
        skip=skip,
        limit=limit,
        api_key=api_key,
        name=name,
        city=city,
        country=country,
    )

    response.headers["X-Total-Count"] = edge_servers["total-count"]

    return edge_servers["elements"]


@router.post(
    "/edge_servers/", tags=["edge_servers"], response_model=schemas.EdgeServerInDBBase
)
def create_edge_server(
    edge_server: schemas.EdgeServerCreateIn,
    db: Session = Depends(get_db),
):
    """
    Create a new edge server.

    Args:
        edge_server (schemas.EdgeServerCreateIn): The data for the new edge server.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.EdgeServerInDBBase: The created edge server.

    Raises:
        HTTPException: If an edge server with the same api_key already exists.
    """
    db_edge_server = crud_edge_server.get_by_api_key(db=db, api_key=edge_server.api_key)
    if db_edge_server is not None:
        raise HTTPException(
            status_code=409,
            detail="Edge Server with the same api_key already registered",
        )

    edge_server_out = schemas.EdgeServerCreateOut(**edge_server.model_dump())
    return crud_edge_server.create(db=db, item=edge_server_out)


@router.get(
    "/edge_servers/{id}",
    tags=["edge_servers"],
    response_model=schemas.EdgeServerInDBBase,
)
def get_edge_server_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve an edge server by its ID.

    Args:
        id (int): The ID of the edge server to retrieve.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        schemas.EdgeServerInDBBase: The edge server information.

    Raises:
        HTTPException: If the ID is not found in the database.
    """
    db_edge_server = crud_edge_server.get_by_id(db=db, id=id)
    if db_edge_server is None:
        raise HTTPException(status_code=404, detail="ID not found")
    return db_edge_server


@router.put(
    "/edge_servers/{id}",
    tags=["edge_servers"],
    response_model=schemas.EdgeServerInDBBase,
)
def update_edge_server(
    id: int,
    edge_server: schemas.EdgeServerUpdateIn,
    db: Session = Depends(get_db),
):
    db_edge_server = crud_edge_server.get_by_id(db=db, id=id)
    if db_edge_server is None:
        raise HTTPException(status_code=404, detail="ID not found")

    edge_server_out = schemas.EdgeServerUpdateOut(**edge_server.model_dump())
    return crud_edge_server.update(db=db, item=edge_server_out, db_item=db_edge_server)


@router.delete("/edge_servers/{id}", tags=["edge_servers"], response_model=bool)
def delete(
    id: int,
    db: Session = Depends(get_db),
):
    db_edge_server = crud_edge_server.get_by_id(db=db, id=id)
    if db_edge_server is None:
        raise HTTPException(status_code=404, detail="ID not found")
    return crud_edge_server.delete(db=db, db_item=db_edge_server)


# AccessLog
from app.db.db_manager import crud_access_log


@router.get(
    "/access_logs/",
    tags=["access_logs"],
    response_model=List[schemas.AccessLogInDBBase],
)
def get_access_logs(
    response: Response,
    skip: int | None = Query(None, ge=0, description="Offset"),
    limit: int | None = Query(None, le=1000, description="Limit"),
    device_node_id: int | None = Query(None, description="Device Node ID"),
    timestamp_start: datetime | None = Query(None, description="Start Date"),
    timestamp_end: datetime | None = Query(None, description="End Date"),
    uid: str | None = Query(None, description="UID"),
    db: Session = Depends(get_db),
):
    access_logs = crud_access_log.get_list(
        db=db,
        skip=skip,
        limit=limit,
        device_node_id=device_node_id,
        start_date=timestamp_start,
        end_date=timestamp_end,
        uid=uid,
    )

    response.headers["X-Total-Count"] = access_logs["total-count"]

    return access_logs["elements"]

# UserAuth
from app.db.db_manager import crud_auth_user


@router.get(
    "/user_auths/", tags=["user_auths"], response_model=List[schemas.UserAuthInDBBase]
)
def get_user_auths(
    response: Response,
    skip: int | None = Query(None, ge=0, description="Offset"),
    limit: int | None = Query(None, le=1000, description="Limit"),
    uid: str | None = Query(None, description="UID"),
    last_access: str | None = Query(None, description="Last Access"),
    last_device_node_id: int | None = Query(None, description="Last Device Node ID"),
    authenticated: bool | None = Query(None, description="Authenticated"),
    db: Session = Depends(get_db),
):
    user_auths = crud_auth_user.get_list(
        db=db,
        skip=skip,
        limit=limit,
        uid=uid,
        last_access=last_access,
        last_device_node_id=last_device_node_id,
        authenticated=authenticated,
    )

    response.headers["X-Total-Count"] = user_auths["total-count"]

    return user_auths["elements"]


@router.post(
    "/user_auths/", tags=["user_auths"], response_model=schemas.UserAuthInDBBase
)
def create_user_auth(
    user_auth: schemas.UserAuthCreateIn,
    db: Session = Depends(get_db),
):
    db_user_auth = crud_auth_user.get_by_uid(db=db, uid=user_auth.uid)
    if db_user_auth is not None:
        raise HTTPException(
            status_code=409, detail="User with the same UID already registered"
        )

    user_auth_out = schemas.UserAuthCreateOut(**user_auth.model_dump())
    return crud_auth_user.create(db=db, item=user_auth_out)


@router.get(
    "/user_auths/{id}", tags=["user_auths"], response_model=schemas.UserAuthInDBBase
)
def get_user_auth_by_id(
    id: int,
    db: Session = Depends(get_db),
):
    db_user_auth = crud_auth_user.get_by_id(db=db, id=id)
    if db_user_auth is None:
        raise HTTPException(status_code=404, detail="ID not found")
    return db_user_auth


@router.put(
    "/user_auths/{id}", tags=["user_auths"], response_model=schemas.UserAuthInDBBase
)
def update_user_auth(
    id: int,
    user_auth: schemas.UserAuthUpdateIn,
    db: Session = Depends(get_db),
):
    db_user_auth = crud_auth_user.get_by_id(db=db, id=id)
    if db_user_auth is None:
        raise HTTPException(status_code=404, detail="ID not found")

    user_auth_out = schemas.UserAuthUpdateOut(**user_auth.model_dump())
    return crud_auth_user.update(db=db, item=user_auth_out, db_item=db_user_auth)


@router.delete("/user_auths/{id}", tags=["user_auths"], response_model=bool)
def delete(
    id: int,
    db: Session = Depends(get_db),
):
    db_user_auth = crud_auth_user.get_by_id(db=db, id=id)
    if db_user_auth is None:
        raise HTTPException(status_code=404, detail="ID not found")
    return crud_auth_user.delete(db=db, db_item=db_user_auth)
