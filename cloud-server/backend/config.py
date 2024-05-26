import os

from typing import List, Optional

from dotenv import load_dotenv

from pydantic_settings import BaseSettings


# Load environment variables with .env
load_dotenv(verbose=True)

# Base settings for the API
class SettingsBase(BaseSettings):
    MODE: str = os.getenv("PROD_OR_DEV")
    API_V1_STR: str = "/nexxgate/api/v1"
    PROJECT_NAME: str = "API NexxGate"
    DESCRIPTION: str = "NexxGate API Service."
    VERSION: str = "0.0.1"

    # Permissão Super Admin que da acesso a todas os modulos do sistema:
    SUPER_USER_PERMISSION: str = "superuser"

    class Config:
        env_file = "../.env"
        env_file_encoding = "utf-8"


# Development Environment Settings - All defined in .env or overridden by environment variables
class SettingsDev(SettingsBase):
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:4200",
        "http://localhost:3000",
        "http://localhost:8080",
    ]

    DB_SERVICE: str = os.getenv("DB_DEV_SERVICE")
    DB_USER: str = os.getenv("DB_DEV_USER")
    DB_PASS: str = os.getenv("DB_DEV_PASS")
    DB_HOST: str = os.getenv("DB_DEV_HOST")
    DB_NAME: str = os.getenv("DB_DEV_NAME")
    DB_SCHEMA: str = os.getenv("DB_DEV_SCHEMA")

    MQTT_USER: str = os.getenv("MQTT_USER_DEV")
    MQTT_PASS: str = os.getenv("MQTT_PASS_DEV")
    MQTT_HOST: str = os.getenv("MQTT_HOST_DEV")
    MQTT_SSL: bool = os.getenv("MQTT_SSL_DEV")
    MQTT_PORT: int = os.getenv("MQTT_PORT_DEV")


# Production Environment Settings - All defined in .env or overridden by environment variables
class SettingsProd(SettingsBase):
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    DB_SERVICE: str = os.getenv("DB_PROD_SERVICE")
    DB_USER: str = os.getenv("DB_PROD_USER")
    DB_PASS: str = os.getenv("DB_PROD_PASS")
    DB_HOST: str = os.getenv("DB_PROD_HOST")
    DB_NAME: str = os.getenv("DB_PROD_NAME")
    DB_SCHEMA: str = os.getenv("DB_PROD_SCHEMA")

    MQTT_USER: str = os.getenv("MQTT_USER_PROD")
    MQTT_PASS: str = os.getenv("MQTT_PASS_PROD")
    MQTT_HOST: str = os.getenv("MQTT_HOST_PROD")
    MQTT_SSL: bool = os.getenv("MQTT_SSL_PROD")
    MQTT_PORT: int = os.getenv("MQTT_PORT_PROD")


# Select the settings based on the operating mode (production or development)
settings = (
    SettingsProd()
    if os.getenv("PROD_OR_DEV") == "PROD"
    else SettingsDev()
)
