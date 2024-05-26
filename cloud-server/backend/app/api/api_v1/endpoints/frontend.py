from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas

from app.dependencies import get_db

router = APIRouter()

# Just checks if it's working for the Cluster
@router.get("/yababab/", tags=["health"], status_code=200)
async def root():
    return {"message": "OK"}
