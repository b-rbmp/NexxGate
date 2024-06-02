import csv
from datetime import datetime
import io
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app import schemas

from app.dependencies import get_db
from app.db.db_manager import crud_auth_user
from app.models import AccessLog
from app.db.db_manager import crud_device, crud_edge_server

router = APIRouter()

# Get updated access list
@router.get("/access_list/", tags=["backend"], response_model=List[schemas.AccessListResponseItem])
def get_access_list(
    response: Response,
    db: Session = Depends(get_db),
):
    # Get all AuthUsers
    auth_users = crud_auth_user.get_list(db=db, skip=0, limit=None, authenticated=True)

    response.headers["X-Total-Count"] = auth_users["total-count"]

    auth_user_elements: List[schemas.UserAuthInDBBase] = auth_users["elements"]

    response_items: List[schemas.AccessListResponseItem] = []

    for auth_user in auth_user_elements:
        response_items.append(schemas.AccessListResponseItem(
            uid=auth_user.uid,
        ))

    return response_items

# Endpoint for sending temporary access logs from an Edge Server, in a .txt file, line by line, with the following format:
# DD/MM/YYYY HH:MM:SS,UID,NodeID,Result
@router.post("/upload-log/", tags=["backend"], status_code=201)
async def upload_log(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    content = content.decode("utf-8")
    
    reader = csv.reader(io.StringIO(content), delimiter=',')
    
    logs_to_add = []
    for row in reader:
        timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S")
        uid = row[1]
        node_id = row[2]
        result = row[3]

        # Convert result to boolean
        if result == "True":
            result = True
        elif result == "False":
            result = False
        else:
            raise HTTPException(status_code=400, detail="Invalid access log result")
        
        # Check if the log already exists in the database
        existing_log = db.query(AccessLog).filter_by(timestamp=timestamp, device_node_id=node_id).first()
        if existing_log is None:
            log = AccessLog(
                device_node_id=node_id,
                timestamp=timestamp,
                uid=uid,
                granted=result
            )
            logs_to_add.append(log)
    
    if logs_to_add:
        db.add_all(logs_to_add)
        db.commit()
    
    return {"message": "Logs uploaded successfully"}





# Endpoint where devices send a GET /device_heartbeat/{api_key} request to update their last_seen field
@router.get("/device_heartbeat/{api_key}", tags=["backend"], status_code=200)
async def device_heartbeat(api_key: str, db: Session = Depends(get_db)):
    # Get device
    device = crud_device.get_by_api_key(db=db, api_key=api_key)

    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update last_seen
    device.last_seen = datetime.now()
    db.commit()
    
    return {"message": "Heartbeat received"}

# Endpoint where Edge Servers send a GET /edge_heartbeat/{api_key} request to update their last_seen field
@router.get("/edge_heartbeat/{api_key}", tags=["backend"], status_code=200)
async def edge_heartbeat(api_key: str, db: Session = Depends(get_db)):
    # Get edge server
    edge_server = crud_edge_server.get_by_api_key(db=db, api_key=api_key)

    if edge_server is None:
        raise HTTPException(status_code=404, detail="Edge Server not found")
    
    # Update last_seen
    edge_server.last_seen = datetime.now()
    db.commit()

    return {"message": "Heartbeat received"}