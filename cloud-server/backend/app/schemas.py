from datetime import datetime
from pydantic.main import BaseModel

from app import models


# Base class for all schemas, making them hashable
class HashableBaseModel(BaseModel):
    def __hash__(self):  # make hashable BaseModel subclass
        return hash((type(self),) + tuple(self.__dict__.values()))


class AuthenticateData(BaseModel):
    """
    Represents authentication data.

    Attributes:
        uid (str, optional): The user ID. Defaults to None.
        node_id (str, optional): The node ID. Defaults to None.
        date (datetime, optional): The date. Defaults to None.
        result (bool, optional): The authentication result. Defaults to None.
        api_key (str, optional): The API key. Defaults to None.
    """
    uid: str | None = None
    node_id: str | None = None
    date: datetime | None = None
    result: bool | None = None
    api_key: str | None = None


# AccessLog
class AccessLogBase(HashableBaseModel):
    """
    Represents the base schema for an access log entry.

    Attributes:
        device_node_id (str | None): The ID of the device node associated with the access log entry.
        timestamp (datetime | None): The timestamp of the access log entry.
        uid (str | None): The UID associated with the access log entry.
        granted (bool | None): Indicates whether access was granted or not.
        edge_server_id (int | None): The ID of the edge server associated with the access log entry.
    """
    device_node_id: str | None = None
    timestamp: datetime | None = None
    uid: str | None = None
    granted: bool | None = None
    edge_server_id: int | None = None


class AccessLogInDBBase(AccessLogBase):
    """
    Represents the base schema for access logs stored in the database.

    This class inherits from the `AccessLogBase` schema and provides additional configuration options.

    Attributes:
        Config (class): Configuration options for the `AccessLogInDBBase` schema.

    """
    class Config:
        from_attributes = True


class AccessLogCreateIn(AccessLogBase):
    """
    Represents the input schema for creating an access log.

    This class inherits from the `AccessLogBase` class.
    """
    pass


class AccessLogCreateOut(AccessLogCreateIn):
    """
    Represents the output schema for creating an access log.

    This class inherits from the `AccessLogCreateIn` class.
    """
    pass


class AccessLogUpdateIn(AccessLogBase):
    """
    Represents the input schema for updating an access log.

    This class inherits from the `AccessLogBase` class.
    """
    pass


class AccessLogUpdateOut(AccessLogUpdateIn):
    """
    Represents the output schema for updating an access log.

    This class inherits from the `AccessLogUpdateIn` class.
    """
    pass


# UserAuth
class UserAuthBase(HashableBaseModel):
    """
    Represents the base schema for user authentication.

    Attributes:
        uid (str | None): The user ID.
        last_access (datetime | None): The timestamp of the last access.
        last_device_node_id (int | None): The ID of the last device node.
        name (str | None): The user's name.
        email (str | None): The user's email.
        authenticated (bool | None): Indicates whether the user is authenticated.
    """
    uid: str | None = None
    last_access: datetime | None = None
    last_device_node_id: int | None = None
    name: str | None = None
    email: str | None = None
    authenticated: bool | None = None


class UserAuthInDBBase(UserAuthBase):
    """
    Represents the base model for user authentication in the database.

    Attributes:
        id (int): The unique identifier for the user.
    """
    id: int
    class Config:
        from_attributes = True


class UserAuthCreateIn(HashableBaseModel):
    """
    Represents the input data required to create a user authentication.

    Attributes:
        uid (str): The unique identifier for the user.
        name (str): The name of the user.
        email (str): The email address of the user.
    """
    uid: str
    name: str
    email: str


class UserAuthCreateOut(UserAuthCreateIn):
    """
    Represents the output schema for creating user authentication.

    This class inherits from the `UserAuthCreateIn` class.
    """
    pass


class UserAuthUpdateIn(UserAuthBase):
    """
    Represents the input model for updating user authentication information.

    This class inherits from the `UserAuthBase` class and can be used to update
    the authentication details of a user.

    Attributes:
        Inherits all attributes from the `UserAuthBase` class.

    """
    pass


class UserAuthUpdateOut(UserAuthUpdateIn):
    """
    Represents the response schema for updating user authentication information.

    Inherits from the `UserAuthUpdateIn` class.
    """
    pass


# Device
class DeviceBase(HashableBaseModel):
    """
    Base class for device schema.

    Attributes:
        node_id (str | None): The ID of the node associated with the device.
        api_key (str | None): The API key for the device.
        last_seen (datetime | None): The timestamp of the last time the device was seen.
        edge_server_id (int | None): The ID of the edge server associated with the device.
    """
    node_id: str | None = None
    api_key: str | None = None
    last_seen: datetime | None = None
    edge_server_id: int | None = None


class DeviceInDBBase(DeviceBase):
    """
    Base class for representing a device in the database.
    Inherits from DeviceBase.
    """
    class Config:
        from_attributes = True


class DeviceCreateIn(DeviceBase):
    """
    Represents the input data required to create a device.

    Attributes:
        node_id (str): The ID of the node associated with the device.
        api_key (str): The API key used for authentication.
        edge_server_id (int): The ID of the edge server associated with the device.
    """
    node_id: str
    api_key: str
    edge_server_id: int


class DeviceCreateOut(DeviceCreateIn):
    """
    Represents the output schema for creating a device.

    This class inherits from the `DeviceCreateIn` class and does not add any additional attributes or methods.
    """
    pass


class DeviceUpdateIn(DeviceBase):
    """
    Represents the input data for updating a device.

    This class inherits from the `DeviceBase` class and can be used to define the
    structure and validation rules for updating a device.

    Attributes:
        Inherits all attributes from the `DeviceBase` class.

    Example usage:
        update_data = DeviceUpdateIn(name="New Name", status="active")
    """
    pass


class DeviceUpdateOut(DeviceUpdateIn):
    """
    Represents the output schema for updating a device.

    This class inherits from the `DeviceUpdateIn` class and does not add any additional attributes or methods.
    """
    pass


# EdgeServer
class EdgeServerBase(HashableBaseModel):
    """
    Represents the base schema for an edge server.

    Attributes:
        api_key (str | None): The API key associated with the edge server.
        name (str | None): The name of the edge server.
        city (str | None): The city where the edge server is located.
        country (str | None): The country where the edge server is located.
        latitude (float | None): The latitude coordinate of the edge server's location.
        longitude (float | None): The longitude coordinate of the edge server's location.
        altitude (float | None): The altitude of the edge server's location.
        last_seen (datetime | None): The timestamp of the last time the edge server was seen.
    """
    api_key: str | None = None
    name: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude: float | None = None
    last_seen: datetime | None = None


class EdgeServerInDBBase(EdgeServerBase):
    """
    Represents the base class for an edge server in the database.
    
    Attributes:
        id (int): The unique identifier for the edge server.
    """
    id: int
    class Config:
        from_attributes = True


class EdgeServerCreateIn(EdgeServerBase):
    """
    Represents the input data required to create an edge server.

    Attributes:
        api_key (str): The API key for the edge server.
        name (str): The name of the edge server.
        city (str): The city where the edge server is located.
        country (str): The country where the edge server is located.
        latitude (float): The latitude coordinate of the edge server's location.
        longitude (float): The longitude coordinate of the edge server's location.
    """
    api_key: str
    name: str
    city: str
    country: str
    latitude: float
    longitude: float
    


class EdgeServerCreateOut(EdgeServerCreateIn):
    """
    Represents the response schema for creating an edge server.

    Inherits from the `EdgeServerCreateIn` class.
    """
    pass


class EdgeServerUpdateIn(EdgeServerBase):
    """
    Represents the input model for updating an edge server.

    This class inherits from the `EdgeServerBase` class and does not add any additional attributes or methods.
    """
    pass


class EdgeServerUpdateOut(EdgeServerUpdateIn):
    """
    Represents the output schema for updating an edge server.

    This class inherits from the `EdgeServerUpdateIn` class and does not add any additional attributes or methods.
    """
    pass



# Responses to the frontend and backend
class AccessListResponseItem(HashableBaseModel):
    """
    Represents an item in the access list response.

    Attributes:
        uid (str): The unique identifier of the item.
    """
    uid: str


class AccessLogsMetricsResponseItem(HashableBaseModel):
    """
    Represents an item in the response for access logs metrics.

    Attributes:
        hour (datetime): The hour of the access log.
        count (int): The count of access logs for the hour.
    """
    hour: datetime
    count: int


class AccessLogsForFrontendResponseItem(HashableBaseModel):
    """
    Represents an item in the response for access logs for the frontend.

    Attributes:
        timestamp (datetime): The timestamp of the access log.
        uid (str): The unique identifier of the user.
        granted (bool): Indicates whether access was granted or not.
        device_node_id (str): The identifier of the device node.
        edge_server_name (str): The name of the edge server.
    """
    timestamp: datetime
    uid: str
    granted: bool
    device_node_id: str
    edge_server_name: str