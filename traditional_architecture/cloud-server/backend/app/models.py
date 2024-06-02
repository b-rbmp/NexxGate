from sqlalchemy import Column, Integer, PrimaryKeyConstraint, String, Boolean, Numeric, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey
from .db.base_class import Base

class EdgeServer(Base):
    __tablename__ = "edge_server"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    api_key = Column(String(20), nullable=False, index=True, unique=True)
    name = Column(String(50), nullable=False, index=True)
    city = Column(String(50), nullable=False, index=True)
    country = Column(String(50), nullable=False, index=True)
    latitude = Column(Numeric(12,6), nullable=True)
    longitude = Column(Numeric(12,6), nullable=True)
    altitude = Column(Numeric(12,6), nullable=True)

    last_seen = Column(DateTime, nullable=True)
    devices = relationship("Device", back_populates="edge_server")


class Device(Base):
    __tablename__ = "device"
    node_id = Column(String(20), primary_key=True, index=True, unique=True)
    api_key = Column(String(20), nullable=False, index=True, unique=True)
    last_seen = Column(DateTime, nullable=True)
    edge_server_id = Column(Integer, ForeignKey('edge_server.id'), nullable=False)
    edge_server = relationship("EdgeServer", back_populates="devices")
    logs = relationship("AccessLog", back_populates="device")
    users = relationship("UserAuth", back_populates="last_device")

class AccessLog(Base):
    __tablename__ = "AccessLog"

    device_node_id = Column(String, ForeignKey('device.node_id'), nullable=False, index=True)
    device = relationship("Device", back_populates="logs")
    timestamp = Column(DateTime, nullable=False, index=True)
    uid = Column(String(20), nullable=False, index=True)
    granted = Column(Boolean, nullable=False, index=True)

    # Make primary key from device_node_id and timestamp
    __table_args__ = (
        PrimaryKeyConstraint('device_node_id', 'timestamp'),
    )

class UserAuth(Base):
    __tablename__ = "UserAuth"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Authenticated
    authenticated = Column(Boolean, nullable=False, index=True, default=False)

    # UID for NFC
    uid = Column(String(20), index=True)
    
    # TODO: Biometric data
    
    # Last access
    last_access = Column(DateTime, nullable=True)
    
    # Last access Device
    last_device_node_id = Column(String, ForeignKey('device.node_id'), nullable=True)
    last_device = relationship("Device", back_populates="users")
    
    # Details
    name = Column(String(50), nullable=False)
    email = Column(String(50), nullable=False)
