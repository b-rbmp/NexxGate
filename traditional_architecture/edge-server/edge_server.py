import paho.mqtt.client as paho
import threading
from datetime import datetime
import json
from pydantic import BaseModel
import api_bridge
import time

cloud_server_connected = False
client_cloud = None

access_list = {}
access_logs_file = "access_log.csv"


# MQTT Callbacks
def on_connect_edge(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("#")


def on_message_edge(client, userdata, msg):
    global cloud_server_connected
    global client_cloud
    print(f"Message received {msg.payload}")
    data = json.loads(msg.payload)

    # Validate incoming data
    try:
        data_authenticate = AuthenticateData(
            uid=data["uid"],
            node_id=data["node_id"],
            date=datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S"),
            result=data["result"],
        )


    except Exception as e:
        print(f"Invalid data: {e}")
        return

    print(
        f"Starting authentication process for {data_authenticate.uid} at {data_authenticate.node_id} on {data_authenticate.date}"
    )
    process_authentication(data_authenticate)


class AuthenticateData(BaseModel):
    uid: str
    node_id: str
    date: datetime
    result: bool

class AuthenticateDataOnlyStr(BaseModel):
    uid: str
    node_id: str
    date: str
    result: str


class AuthenticatedData(BaseModel):
    uid: str
    node_id: str
    result: bool


def write_access_to_file(data: AuthenticateData):
    global access_logs_file
    with open(access_logs_file, "a") as file:
        # Format:  %Y-%m-%d %H:%M:%S,user1,NodeA,true
        date_str = data.date.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{date_str},{data.uid},{data.node_id},{data.result}\n")


def process_authentication(data: AuthenticateData):
    global access_list
    global client
    
    uid = data.uid
    node_id = data.node_id
    result = data.result
    date = data.date

    new_result = data.result

    # If negative result, check local access list
    if not result and uid in access_list:
        response_topic = f"/allow_authentication"
        authenticated_info = AuthenticatedData(uid=uid, result=True, node_id=node_id)
        new_result = True
        client.publish(response_topic, json.dumps(authenticated_info.model_dump()))

        print(f"Authenticated {uid} at {node_id} on {date}")

    # Log every authentication attempt
    new_data = AuthenticateData(uid=uid, node_id=node_id, date=date, result=new_result)
    write_access_to_file(new_data)
    
    # Date is converted to format 2024-05-30 18:27:25
    date_str = new_data.date.strftime("%Y-%m-%d %H:%M:%S")
    data_authenticate_only_str = AuthenticateDataOnlyStr(
            uid=new_data.uid,
            node_id=new_data.node_id,
            date=date_str,
            result=str(new_data.result),
        )

    if cloud_server_connected:
        # Publish to /nexxgate/access
        client_cloud.publish("/nexxgate/access", json.dumps(data_authenticate_only_str.model_dump()))


# Update logs to cloud every hour
def update_logs_to_cloud():
    global cloud_server_connected
    global access_logs_file
    print("Sending logs to cloud")

    # If file not found, create it
    try:
        with open(access_logs_file, "r") as file:
            pass
    except FileNotFoundError:
        with open(access_logs_file, "w") as file:
            pass


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
        access_list.update({access["uid"]: True})

    threading.Timer(300, update_access_list).start()

def heartbeat_cloud():
    global cloud_server_connected
    print("Sending heartbeat to cloud")

    cloud_server_connected = api_bridge.check_cloud_connection()

    if cloud_server_connected:
        print("Cloud server connected")
        # Send heartbeat to cloud
        success = api_bridge.send_edge_heartbeat()
        if success:
            print("Heartbeat sent to cloud")
        else:
            print("Failed to send heartbeat to cloud")

    # Publish to the heartbeat every half hour
    threading.Timer(1800, heartbeat_cloud).start()

heartbeat_cloud()  # Start periodic updates
# Wait 5 seconds for the server to start below
time.sleep(5)

update_access_list()  # Start periodic updates
update_logs_to_cloud()  # Start periodic updates

# Initialize MQTT Client
client = paho.Client(
    client_id=None, userdata=None, protocol=paho.MQTTv311, clean_session=True
)
client.on_connect = on_connect_edge
client.on_message = on_message_edge
client.connect("localhost", 1883)
client.loop_start()

# Initialize second MQTT Client for publishing to cloud
client_cloud = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client_cloud.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)

def on_connect_cloud(client, userdata, flags, rc, properties=None):
    print("Connected to cloud with result code " + str(rc))

client_cloud.on_connect = on_connect_cloud
# Set password and username
client_cloud.username_pw_set("nexxgateuser", "Nexxgate1")
client_cloud.connect("40f10495a5e44f659aa663378f527c6e.s1.eu.hivemq.cloud", 8883)
client_cloud.loop_start()
