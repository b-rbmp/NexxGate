import base64
import os
from typing import List
import paho.mqtt.client as paho
import threading
from datetime import datetime, timedelta
from collections import Counter
import json
from pydantic import BaseModel
import api_bridge
import time
from dotenv import load_dotenv
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# Constants
API_KEY = "aj1jD9mf11"

EDGE_MQTT_BROKER = "localhost"
EDGE_MQTT_PORT = 8883
EDGE_MQTT_CA_CERT = "D:\\Documents\\GitHub\\NexxGate\\edge-server\\edge_certs\\ca_cert.pem"
EDGE_MQTT_CERT = "D:\\Documents\\GitHub\\NexxGate\\edge-server\\edge_certs\\client_cert.pem"
EDGE_MQTT_KEY = "D:\\Documents\\GitHub\\NexxGate\\edge-server\\edge_certs\\client_key.pem"
EDGE_MQTT_TLS_VERSION = paho.ssl.PROTOCOL_TLS

CLOUD_MQTT_BROKER = "40f10495a5e44f659aa663378f527c6e.s1.eu.hivemq.cloud"
CLOUD_MQTT_PORT = 8883
ACCESS_LOG_FILE = "access_log.txt"
PERIOD_UPDATE_ACCESS_LIST = 300  # 5 minutes
PERIOD_UPDATE_LOGS = 3600 * 24 * 7  # 1 week
PERIOD_HEARTBEAT = 1800  # 30 minutes
VOTE_TIMEOUT = 10  # 10 seconds
LIMIT_ACCESS_LIST_DEVICES = 100
LOCKOUT_PERIOD = timedelta(seconds=10) # 10 seconds lockout period
CLOUD_KEYS_FOLDER = "D:\\Documents\\GitHub\\NexxGate\\edge-server\\cloud_keys"

# Topics
AUTHENTICATE_TOPIC = "/authenticate"
ALLOW_AUTHENTICATE_TOPIC = "/allow_authentication"
MAJORITY_VOTE_TOPIC = "/majority_vote"
VOTE_RESPONSE_TOPIC = "/vote_response"
ACCESS_LIST_TOPIC = "/access_list"
REMOVE_UID_TOPIC = "/remove_uid"
REQUEST_ACCESS_LIST_TOPIC = "/request_access_list"
RESPONSE_ACCESS_LIST_TOPIC = "/response_access_list"

cloud_server_connected = False
client_cloud = None

access_list = []
votes_received = []

# Initialize empty cloud private key
cloud_private_key = None

# Load private key for cloud
with open(CLOUD_KEYS_FOLDER+"\\private_key.pem", "rb") as key_file:
    cloud_private_key = serialization.load_pem_private_key(key_file.read(), password=None)

class LockoutData(BaseModel):
    access_time: datetime
    node_id: str

# Dictionary to store the last access time and node_id of each UID for the lockout period mechanism
uid_access_times_and_node_id: dict[str, LockoutData] = {}

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
    api_key: str


class AuthenticatedData(BaseModel):
    uid: str
    node_id: str
    result: bool
    signature: str

class AccessListData(BaseModel):
    uids: List[str]
    signature: str

class RemoveUidData(BaseModel):
    uid: str
    signature: str


# MQTT Callbacks
def on_connect_edge(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(REQUEST_ACCESS_LIST_TOPIC)
    client.subscribe(AUTHENTICATE_TOPIC)
    client.subscribe(VOTE_RESPONSE_TOPIC)
    client.subscribe(MAJORITY_VOTE_TOPIC)


# MQTT on_message callback
def on_message_edge(client, userdata, msg):
    global cloud_server_connected, client_cloud, is_generating_keys

    print(f"Message received on topic {msg.topic}: {msg.payload}")

    if msg.topic == REQUEST_ACCESS_LIST_TOPIC:
        handle_update_request(msg.payload)
    elif msg.topic == AUTHENTICATE_TOPIC:
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
    elif msg.topic == VOTE_RESPONSE_TOPIC:
        handle_vote_response(msg.payload)
    elif msg.topic == MAJORITY_VOTE_TOPIC:
        client.publish(VOTE_RESPONSE_TOPIC, json.dumps(access_list))

# Function to sign data
def sign_data(data):
    global cloud_private_key
    
    signature = cloud_private_key.sign(
        data,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode()

# Function to create signed UID list with public key
def create_signed_uid_list(uids: List[str]):
    global cloud_private_key
    uid_list_json = json.dumps(uids).encode('utf-8')
    signature = sign_data(uid_list_json)
    return {"uids": uids, "signature": signature}


# Function to publish a signed UID list
def publish_signed_uid_list(uids: List[str], topic: str):
    global client, cloud_private_key
    signed_uid_list = create_signed_uid_list(uids)
    client.publish(topic, json.dumps(signed_uid_list))

# Function to count UID frequency in logs
def count_uid_frequency():
    global ACCESS_LOG_FILE
    if not os.path.exists(ACCESS_LOG_FILE):
        return []

    with open(ACCESS_LOG_FILE, "r") as file:
        logs = file.readlines()

    past_week = datetime.now() - timedelta(days=7)
    uid_counter = Counter()

    for log in logs:
        date_str, uid, node_id, result, api_key = log.strip().split(",")
        log_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

        if log_date >= past_week:
            uid_counter[uid] += 1

    return uid_counter.most_common(100)

def get_100_most_frequent_uids_in_access_list() -> List[str]:
    global access_list
    uid_frequency = count_uid_frequency()
    most_frequent_uids = [uid for uid, _ in uid_frequency]

    # Get the 100 most frequent UIDs that are in the access list
    most_frequent_uids_in_access_list = [
        uid for uid in most_frequent_uids if uid in access_list
    ]

    # If the frequency of the most frequent UIDs in the access list is less than 100, add UIDs from the access list that are not in the logs until
    # it reaches 100
    if len(most_frequent_uids_in_access_list) < LIMIT_ACCESS_LIST_DEVICES:
        for uid in access_list:
            if uid not in most_frequent_uids_in_access_list:
                most_frequent_uids_in_access_list.append(uid)
                if len(most_frequent_uids_in_access_list) == LIMIT_ACCESS_LIST_DEVICES:
                    break

    return most_frequent_uids_in_access_list



def update_access_list_from_request():
    global access_list, client

    # Get the 100 most frequent UIDs in the access list
    most_frequent_uids_in_access_list = get_100_most_frequent_uids_in_access_list()

    # Publish the data signed with the private key
    response_signed = create_signed_uid_list(most_frequent_uids_in_access_list)

    access_data = AccessListData(uids=response_signed["uids"], signature=response_signed["signature"])

    client.publish(RESPONSE_ACCESS_LIST_TOPIC, json.dumps(access_data.model_dump()))


# Handle update request
def handle_update_request(payload):
    if payload == b"update":
        update_access_list_from_request()


def write_access_to_file(data: AuthenticateData):
    global ACCESS_LOG_FILE
    with open(ACCESS_LOG_FILE, "a") as file:
        # Format:  %Y-%m-%d %H:%M:%S,user1,NodeA,true
        date_str = data.date.strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{date_str},{data.uid},{data.node_id},{data.result},{API_KEY}\n")


def lockout_uid(uid):
    global access_list, client
    if uid in access_list:
        access_list.remove(uid)

        # Create the signed UID removal data
        remove_uid_data = RemoveUidData(uid=uid, signature=sign_data(uid.encode('utf-8')))
        client.publish(REMOVE_UID_TOPIC, json.dumps(remove_uid_data.model_dump()))

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
        response_topic = ALLOW_AUTHENTICATE_TOPIC

        # Sign the data
        authenticated_info = AuthenticatedData(uid=uid, result=True, node_id=node_id, signature=sign_data(uid.encode('utf-8')))
        new_result = True
        # Lockout mechanism
        if new_result:
            if uid in uid_access_times_and_node_id:
                last_access_time_and_node_id = uid_access_times_and_node_id[uid]
                if date - last_access_time_and_node_id.access_time < LOCKOUT_PERIOD and last_access_time_and_node_id.node_id != node_id:
                    print(f"Lockout triggered for {uid}")
                    lockout_uid(uid)
                    new_result = False
                else:
                    client.publish(response_topic, json.dumps(authenticated_info.model_dump()))
                    print(f"Authenticated {uid} at {node_id} on {date}")
            else:
                client.publish(response_topic, json.dumps(authenticated_info.model_dump()))
                print(f"Authenticated {uid} at {node_id} on {date}")


    # Log every authentication attempt
    new_data = AuthenticateData(uid=uid, node_id=node_id, date=date, result=new_result)
    write_access_to_file(new_data)

    # Lockout mechanism
    if result:
        if uid in uid_access_times_and_node_id:
            last_access_time_and_node_id = uid_access_times_and_node_id[uid]
            if date - last_access_time_and_node_id.access_time < LOCKOUT_PERIOD and last_access_time_and_node_id.node_id != node_id:
                print(f"Lockout triggered for {uid}")
                lockout_uid(uid)
                new_result = False
        
    uid_access_times_and_node_id[uid] = LockoutData(access_time=date, node_id=node_id)

    # Date is converted to format 2024-05-30 18:27:25
    date_str = new_data.date.strftime("%Y-%m-%d %H:%M:%S")
    data_authenticate_only_str = AuthenticateDataOnlyStr(
        uid=new_data.uid,
        node_id=new_data.node_id,
        date=date_str,
        result=str(new_data.result),
        api_key=API_KEY,
    )

    if cloud_server_connected:
        # Publish to /nexxgate/access
        client_cloud.publish(
            "/nexxgate/access", json.dumps(data_authenticate_only_str.model_dump())
        )





# Update logs to cloud every hour
def update_logs_to_cloud():
    global cloud_server_connected
    global ACCESS_LOG_FILE
    print("Sending logs to cloud")

    # If file not found, create it
    try:
        with open(ACCESS_LOG_FILE, "r") as file:
            pass
    except FileNotFoundError:
        with open(ACCESS_LOG_FILE, "w") as file:
            pass

    if cloud_server_connected:
        if api_bridge.upload_log_file(ACCESS_LOG_FILE):
            print("Logs sent to cloud")

            # Clear the logs file
            with open(ACCESS_LOG_FILE, "w") as file:
                pass
        else:
            print("Failed to send logs to cloud")
    threading.Timer(PERIOD_UPDATE_LOGS, update_logs_to_cloud).start()


# Function that updates the access list with a majority vote mechanism in case of cloud server failure
def update_access_list_schedule():
    # Update access list from a source or modify it
    global access_list, client
    print("Updating access list")

    response_access_list = api_bridge.get_updated_access_list()

    if response_access_list is None:
        print("Failed to synchronize with cloud server. Starting majority vote...")
        response_access_list = start_majority_vote()
    else:
        # For each access in the response, update the access list
        access_list = []
        for access in response_access_list:
            access_list.append(access["uid"])

        most_frequent_uids_in_access_list = get_100_most_frequent_uids_in_access_list()

        # Publish the data signed with the private key
        response_signed = create_signed_uid_list(most_frequent_uids_in_access_list)

        access_data = AccessListData(uids=response_signed["uids"], signature=response_signed["signature"])

        client.publish(ACCESS_LIST_TOPIC, json.dumps(access_data.model_dump()))
        print("Access list updated")

        

    threading.Timer(PERIOD_UPDATE_ACCESS_LIST, update_access_list_schedule).start()


# Start majority vote among edge servers
def start_majority_vote():
    global votes_received, client, access_list
    votes_received = []
    client.publish(MAJORITY_VOTE_TOPIC, json.dumps(access_list))
    threading.Timer(VOTE_TIMEOUT, conclude_majority_vote).start()


# Handle vote response
def handle_vote_response(payload):
    global votes_received
    votes_received.append(payload)


def conclude_majority_vote():
    global access_list, votes_received, client
    if not votes_received:
        print("No votes received, using local access list.")
        return

    # Count votes for each access list. Each vote is a b'["A", "B"]' string
    votes = Counter(votes_received)
    majority_vote = votes.most_common(1)[0][0]
    print(f"Majority vote: {majority_vote}")

    # Convert majority vote in format b'["A", "B"]' to ["A", "B"]
    majority_vote = json.loads(majority_vote)

    # Update access list
    access_list = majority_vote

    most_frequent_uids_in_access_list = get_100_most_frequent_uids_in_access_list()
    
    # Publish the data signed with the private key
    response_signed = create_signed_uid_list(most_frequent_uids_in_access_list)

    access_data = AccessListData(uids=response_signed["uids"], signature=response_signed["signature"])

    client.publish(ACCESS_LIST_TOPIC, json.dumps(access_data.model_dump()))
    print("Majority vote concluded. Access list updated.")


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
    threading.Timer(PERIOD_HEARTBEAT, heartbeat_cloud).start()


heartbeat_cloud()  # Start periodic updates
# Wait 5 seconds for the server to start below
time.sleep(5)

update_logs_to_cloud()  # Start periodic updates

# Initialize MQTT Client
client = paho.Client(
    client_id=None, userdata=None, protocol=paho.MQTTv311, clean_session=True
)
client.tls_set(
    ca_certs=EDGE_MQTT_CA_CERT,
    certfile=EDGE_MQTT_CERT,
    keyfile=EDGE_MQTT_KEY,
    tls_version=EDGE_MQTT_TLS_VERSION,
)
client.on_connect = on_connect_edge
client.on_message = on_message_edge
client.connect(EDGE_MQTT_BROKER, EDGE_MQTT_PORT)
client.loop_start()

# Initialize second MQTT Client for publishing to cloud
client_cloud = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client_cloud.tls_set(tls_version=paho.ssl.PROTOCOL_TLS)


def on_connect_cloud(client, userdata, flags, rc, properties=None):
    print("Connected to cloud with result code " + str(rc))


client_cloud.on_connect = on_connect_cloud
# Set password and username
client_cloud.username_pw_set("nexxgateuser", "Nexxgate1")
client_cloud.connect(CLOUD_MQTT_BROKER, CLOUD_MQTT_PORT)
client_cloud.loop_start()

update_access_list_schedule()  # Start periodic updates