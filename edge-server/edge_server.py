import time
import paho.mqtt.client as paho
from paho import mqtt
import threading
from datetime import datetime
import json
from pydantic import BaseModel
import requests
import api_bridge

cloud_server_connected = False
client_cloud = None

access_list = {} 
access_logs_file = "access_log.csv"



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
        if cloud_server_connected:
            # Publish to /nexxgate/access
            client_cloud.publish("/nexxgate/access", json.dumps(data.model_dump()))


    except Exception as e:
        print(f"Invalid data: {e}")
        return
    
    print(f"Starting authentication process for {data.uid} at {data.node_id} on {data.date}")
    process_authentication(data)

class AuthenticateData(BaseModel):
    uid: str
    node_id: str
    date: datetime
    result: bool

class AuthenticatedData(BaseModel):
    uid: str
    node_id: str
    result: bool

def write_access_to_file(data: AuthenticateData):
    with open(access_logs_file, "a") as file:
        # Format:  25/05/2024 14:30:00,user1,NodeA,true
        file.write(f"{data.date},{data.uid},{data.node_id},{data.result}\n")

def process_authentication(data: AuthenticateData):
    uid = data.uid
    node_id = data.node_id
    result = data.result
    date = data.date
    
    # Log every authentication attempt
    write_access_to_file(data)

    # If negative result, check local access list
    if not result and uid in access_list:
        response_topic = f"/allow_authentication"
        authenticated_info = AuthenticatedData(uid=uid, result=True, node_id=node_id)
        client.publish(response_topic, json.dumps(authenticated_info.model_dump()))

        print(f"Authenticated {uid} at {node_id} on {date}")

# Update logs to cloud every hour
def update_logs_to_cloud():
    print("Sending logs to cloud")

    if cloud_server_connected:
        if api_bridge.upload_log_file(access_logs_file):
            print("Logs sent to cloud")

            # Clear the logs file
            with open(access_logs_file, "w") as file:
                pass
        else:
            print("Failed to send logs to cloud")
    threading.Timer(3600, update_logs_to_cloud).start()


def update_access_list():
    # Update access list from a source or modify it
    global access_list
    print("Updating access list")

    response_access_list = api_bridge.get_updated_access_list()

    if response_access_list is None:
        print("Failed to update access list")
        return
    
    # For each access in the response, update the access list
    for access in response_access_list:
        access_list.update({access.uid: True})

    threading.Timer(300, update_access_list).start()

def heartbeat_cloud():
    global cloud_server_connected
    print("Sending heartbeat to cloud")

    cloud_server_connected = api_bridge.check_cloud_connection()
        
    if cloud_server_connected:
        print("Cloud server connected")
        # Send heartbeat to cloud
        api_bridge.send_edge_heartbeat()

        # Publish to the heartbeat 
    threading.Timer(20, heartbeat_cloud).start()

heartbeat_cloud()  # Start periodic updates
# Wait 5 seconds for the server to start below
time.sleep(5)

update_access_list()  # Start periodic updates
update_logs_to_cloud()  # Start periodic updates

# Initialize MQTT Client
client = paho.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("localhost", 1883, 60)
client.loop_start()

# Initialize second MQTT Client for publishing to cloud
client_cloud = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client_cloud.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)

# Set password and username
client_cloud.username_pw_set("nexxgateuser", "Nexxgate1")
client_cloud.connect("40f10495a5e44f659aa663378f527c6e.s1.eu.hivemq.cloud", 8883)
client_cloud.loop_start()



