import datetime
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas, models
from app.db.db_manager import crud_access_log
from app.dependencies import get_db

router = APIRouter()

# Function that returns metrics of access logs per hour (how many people entered per hour) on the past 24 hours
@router.get("/metrics/access-logs/", tags=["metrics"])
async def access_logs_metrics(db: Session = Depends(get_db)):
    # Current time
    current_time = datetime.datetime.now()
    # 24 hours ago
    start_date = current_time - datetime.timedelta(hours=24)

    # Get all access logs
    access_logs: List[models.AccessLog] = crud_access_log.get_list(db=db, skip=0, limit=100000, start_date=start_date, end_date=current_time)["elements"]
    

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

    return access_logs_metrics