import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app import schemas, models
from app.db.db_manager import crud_access_log
from app.dependencies import get_db

router = APIRouter()

# Function that returns metrics of access logs per hour (how many people entered per hour) on the past 24 hours
@router.get("/metrics/access-logs/", tags=["metrics"], response_model=List[schemas.AccessLogsMetricsResponseItem])
async def access_logs_metrics(db: Session = Depends(get_db)):
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
        access_logs_for_frontend.append(
            schemas.AccessLogsForFrontendResponseItem(
                device_node_id=access_log.device_node_id,
                timestamp=access_log.timestamp,
                uid=access_log.uid,
                granted=access_log.granted,
                edge_server_name="TODO",
            )
        )

    response.headers["X-Total-Count"] = access_logs["total-count"]

    return access_logs_for_frontend
