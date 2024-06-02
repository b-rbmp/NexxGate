from fastapi import APIRouter

router = APIRouter()

# Just checks if it's working for the Cluster
@router.get("/health-check/", tags=["health"], status_code=200)
async def root():
    return {"message": "OK"}
