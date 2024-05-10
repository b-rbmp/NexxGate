import paho.mqtt.client as mqtt
import threading
from datetime import datetime
import json
from pydantic import BaseModel

# MQTT Callbacks
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe("/authenticate")

def on_message(client, userdata, msg):
    print(f"Message received {msg.payload}")
    data = json.loads(msg.payload)

    # Validate incoming data
    try:
        data = AuthenticateData(
            uid=data['uid'],
            node_id=data['node_id'],
            date=datetime.strptime(data['date'], "%Y-%m-%d %H:%M:%S"),
            result=data['result']
        )
    except Exception as e:
        print(f"Invalid data: {e}")
        return
    
    print(f"Starting authentication process for {data.uid} at {data.node_id} on {data.date}")
    process_authentication(data)

access_list = {'A5EF1877': True}  # Mock access list
access_logs = []

class AuthenticateData(BaseModel):
    uid: str
    node_id: str
    date: datetime
    result: bool

class AuthenticatedData(BaseModel):
    uid: str
    node_id: str
    result: bool

def process_authentication(data: AuthenticateData):
    uid = data.uid
    node_id = data.node_id
    result = data.result
    date = data.date
    
    # Log every authentication attempt
    access_logs.append(data)

    # If negative result, check local access list
    if not result and uid in access_list:
        response_topic = f"/allow_authentication"
        authenticated_info = AuthenticatedData(uid=uid, result=True, node_id=node_id)
        client.publish(response_topic, json.dumps(authenticated_info.model_dump()))

        print(f"Authenticated {uid} at {node_id} on {date}")

# Update logs to cloud every hour
def update_logs_to_cloud():
    global access_logs
    print("Sending logs to cloud")
    access_logs = []
    threading.Timer(3600, update_logs_to_cloud).start()


def update_access_list():
    # Update access list from a source or modify it
    global access_list
    print("Updating access list")
    access_list.update({'UID67890': True})  # Mock update
    threading.Timer(300, update_access_list).start()


update_access_list()  # Start periodic updates
update_logs_to_cloud()  # Start periodic updates

# Initialize MQTT Client
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()
