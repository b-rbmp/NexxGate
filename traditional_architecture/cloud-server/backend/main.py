from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


#from .dependencies import get_query_token
from app.api.api_v1.api import api_router
from config import settings
from app.core import mqtt

# API initialization with its settings
app = FastAPI(title=settings.PROJECT_NAME, description=settings.DESCRIPTION, version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/openapi.json", docs_url=f"{settings.API_V1_STR}/docs", redoc_url=f"{settings.API_V1_STR}/redoc")

# Allow all CORS communication through the origins defined in the settings in set 
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-total-count"],
    )

# Include the API Router with the prefix defined in the settings
app.include_router(api_router, prefix=settings.API_V1_STR)

mqtt.client.loop_start()