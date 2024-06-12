import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app import schemas, models
from app.db.db_manager import crud_access_log, crud_edge_server
from app.dependencies import get_db

router = APIRouter()

# Function that returns metrics of access logs per hour (how many people entered per hour) on the past 24 hours
@router.get("/metrics/access-logs/", tags=["metrics"], response_model=List[schemas.AccessLogsMetricsResponseItem])
async def access_logs_metrics(db: Session = Depends(get_db)):
    """
    Retrieve access logs metrics for the past 24 hours.

    Parameters:
    - db: The database session.

    Returns:
    - List of AccessLogsMetricsResponseItem: A list of response items containing the hour and the count of people that entered during that hour.
    """
    # Current time
    current_time = datetime.datetime.now()
    # 24 hours ago
    start_date = current_time - datetime.timedelta(hours=24)

    # Get all access logs
    access_logs: List[models.AccessLog] = crud_access_log.get_list(db=db, skip=0, limit=100000, start_date=start_date, end_date=current_time, granted=True)["elements"]
    
    # Dictionary to store the number of people that entered per hour, storing always the full datetime but with the hour 14:00:00, 15:00:00, etc.
    access_logs_metrics = {}
    for access_log in access_logs:
        # Get the hour of the access log
        hour = access_log.timestamp.replace(minute=0, second=0, microsecond=0)
        # If the hour is not in the dictionary, add it
        if hour not in access_logs_metrics:
            access_logs_metrics[hour] = 0
        # Add one person to the hour
        access_logs_metrics[hour] += 1

    # Fill the missing hours with 0
    for i in range(24):
        hour = current_time.replace(hour=i, minute=0, second=0, microsecond=0)
        if hour not in access_logs_metrics:
            access_logs_metrics[hour] = 0

    # Sort the dictionary by the hour
    access_logs_metrics = dict(sorted(access_logs_metrics.items()))

    # Create the response items
    access_logs_metrics_response_items: List[schemas.AccessLogsMetricsResponseItem] = []
    for hour, count in access_logs_metrics.items():
        access_logs_metrics_response_items.append(schemas.AccessLogsMetricsResponseItem(
            hour=hour,
            count=count
        ))

    return access_logs_metrics_response_items

@router.get("/metrics/all-accesses/", tags=["metrics"], response_model=int)
async def all_accesses(db: Session = Depends(get_db)):
    """
    Retrieve the total count of all accesses.

    Parameters:
    - db: The database session.

    Returns:
    - int: The total count of all accesses.
    """
    return crud_access_log.get_list(db=db, skip=0, limit=1000000, start_date=None, end_date=None, granted=True)["total-count"]


@router.get(
    "/access_logs_frontend/",
    tags=["access_logs"],
    response_model=List[schemas.AccessLogsForFrontendResponseItem],
)
async def get_access_logs(
    response: Response,
    skip: int | None = Query(None, ge=0, description="Offset"),
    limit: int | None = Query(None, le=1000, description="Limit"),
    device_node_id: int | None = Query(None, description="Device Node ID"),
    timestamp_start: datetime.datetime | None = Query(None, description="Start Date"),
    timestamp_end: datetime.datetime | None = Query(None, description="End Date"),
    uid: str | None = Query(None, description="UID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve access logs for the frontend.

    This endpoint returns a list of access logs for the frontend application.
    The logs can be filtered based on various parameters such as offset, limit,
    device node ID, start date, end date, and UID.

    Parameters:
    - response: The response object.
    - skip: The offset value for pagination (default: None).
    - limit: The limit value for pagination (default: None).
    - device_node_id: The ID of the device node to filter logs (default: None).
    - timestamp_start: The start date to filter logs (default: None).
    - timestamp_end: The end date to filter logs (default: None).
    - uid: The UID to filter logs (default: None).
    - db: The database session dependency.

    Returns:
    - access_logs_for_frontend: A list of access logs for the frontend application.

    """
    access_logs = crud_access_log.get_list(
        db=db,
        skip=skip,
        limit=limit,
        device_node_id=device_node_id,
        start_date=timestamp_start,
        end_date=timestamp_end,
        uid=uid,
    )

    # Fill the AccessLogForFrontendResponseItem
    access_logs_original: List[models.AccessLog] = access_logs["elements"]
    access_logs_for_frontend: List[schemas.AccessLogsForFrontendResponseItem] = []
    for access_log in access_logs_original:
        # For each edge server, get the name
        edge_server_id = access_log.edge_server_id
        edge_server = crud_edge_server.get_by_id(db=db, id=edge_server_id)

        access_logs_for_frontend.append(
            schemas.AccessLogsForFrontendResponseItem(
                device_node_id=access_log.device_node_id,
                timestamp=access_log.timestamp,
                uid=access_log.uid,
                granted=access_log.granted,
                edge_server_name=edge_server.name,
            )
        )

    response.headers["X-Total-Count"] = access_logs["total-count"]

    return access_logs_for_frontend
