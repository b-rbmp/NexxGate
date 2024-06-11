from datetime import datetime
from pydantic.main import BaseModel

from app import models


# Base class for all schemas, making them hashable
class HashableBaseModel(BaseModel):
    def __hash__(self):  # make hashable BaseModel subclass
        return hash((type(self),) + tuple(self.__dict__.values()))


class AuthenticateData(BaseModel):
    uid: str | None = None
    node_id: str | None = None
    date: datetime | None = None
    result: bool | None = None
    api_key: str | None = None


# AccessLog
class AccessLogBase(HashableBaseModel):
    device_node_id: str | None = None
    timestamp: datetime | None = None
    uid: str | None = None
    granted: bool | None = None
    edge_server_id: int | None = None


class AccessLogInDBBase(AccessLogBase):
    class Config:
        from_attributes = True


class AccessLogCreateIn(AccessLogBase):
    pass


class AccessLogCreateOut(AccessLogCreateIn):
    pass


class AccessLogUpdateIn(AccessLogBase):
    pass


class AccessLogUpdateOut(AccessLogUpdateIn):
    pass


# UserAuth
class UserAuthBase(HashableBaseModel):
    uid: str | None = None
    last_access: datetime | None = None
    last_device_node_id: int | None = None
    name: str | None = None
    email: str | None = None
    authenticated: bool | None = None


class UserAuthInDBBase(UserAuthBase):
    id: int
    class Config:
        from_attributes = True


class UserAuthCreateIn(HashableBaseModel):
    uid: str
    name: str
    email: str


class UserAuthCreateOut(UserAuthCreateIn):
    pass


class UserAuthUpdateIn(UserAuthBase):
    pass


class UserAuthUpdateOut(UserAuthUpdateIn):
    pass


# Device
class DeviceBase(HashableBaseModel):
    node_id: str | None = None
    api_key: str | None = None
    last_seen: datetime | None = None
    edge_server_id: int | None = None


class DeviceInDBBase(DeviceBase):
    class Config:
        from_attributes = True


class DeviceCreateIn(DeviceBase):
    node_id: str
    api_key: str
    edge_server_id: int


class DeviceCreateOut(DeviceCreateIn):
    pass


class DeviceUpdateIn(DeviceBase):
    pass


class DeviceUpdateOut(DeviceUpdateIn):
    pass


# EdgeServer
class EdgeServerBase(HashableBaseModel):
    api_key: str | None = None
    name: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    last_seen: datetime | None = None


class EdgeServerInDBBase(EdgeServerBase):
    id: int
    class Config:
        from_attributes = True


class EdgeServerCreateIn(EdgeServerBase):
    api_key: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    


class EdgeServerCreateOut(EdgeServerCreateIn):
    pass


class EdgeServerUpdateIn(EdgeServerBase):
    pass


class EdgeServerUpdateOut(EdgeServerUpdateIn):
    pass



# Responses to the frontend and backend
class AccessListResponseItem(HashableBaseModel):
    uid: str
    # biometric_data: str


class AccessLogsMetricsResponseItem(HashableBaseModel):
    hour: datetime
    count: int


class AccessLogsForFrontendResponseItem(HashableBaseModel):
    timestamp: datetime
    uid: str
    granted: bool
    device_node_id: str
    edge_server_name: str