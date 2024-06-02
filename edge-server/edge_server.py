import base64
import os
import time
from typing import List
import paho.mqtt.client as mqtt
import json
import threading
import api_bridge
import datetime
from collections import Counter
from dotenv import load_dotenv
from pydantic import BaseModel
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

load_dotenv()

# Constants
EDGE_MQTT_BROKER = "localhost"
EDGE_MQTT_PORT = 1883
ACCESS_LIST_TOPIC = "/access_list"
REQUEST_ACCESS_LIST_TOPIC = "/request_access_list"
RESPONSE_ACCESS_LIST_TOPIC = "/response_access_list"
AUTHENTICATE_TOPIC = "/authenticate"
ALLOW_AUTHENTICATE_TOPIC = "/allow_authenticate"
LOG_FILE = "access_log.txt"
PERIOD_UPDATE_ACCESS_LIST = 300  # 5 minutes
PERIOD_UPDATE_LOGS = 3600 * 24 * 7 # 1 week
PERIOD_HEARTBEAT = 1800  # 30 minutes
PERIOD_UPDATE_KEYS = 3600  # 1 hour
MAJORITY_VOTE_TOPIC = "/majority_vote"
VOTE_RESPONSE_TOPIC = "/vote_response"
KEY_GENERATION_TOPIC = "/key_generation"
KEY_GENERATION_TIMEOUT = 10  # 10 seconds
VOTE_TIMEOUT = 10  # 10 seconds

# Globals
access_list = []
cloud_server_connected = False
client_cloud = None
client = None
votes_received = []
is_generating_keys = False


# Generate deterministic RSA key pair based on seed
def generate_rsa_key_pair(seed):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()
    return private_key, public_key

# Initialize empty keys
private_key = None
public_key = None

# Types
class AuthenticateData(BaseModel):
    encrypted_uid: str
    node_id: str
    date: datetime.datetime
    result: bool

class AuthenticateDataLog(BaseModel):
    uid: str
    node_id: str
    date: str
    result: str


class AuthenticatedData(BaseModel):
    encrypted_uid: str
    node_id: str
    result: bool

class AccessListResponse(BaseModel):
    access_list: List[str]
    public_key: str


def write_access_to_file(data: AuthenticateDataLog):
    with open(LOG_FILE, "a") as file:
        # Format:  %Y-%m-%d %H:%M:%S,user1,NodeA,true
        file.write(f"{data.date},{data.uid},{data.node_id},{data.result}\n")


# Function to count UID frequency in logs
def count_uid_frequency():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, "r") as file:
        logs = file.readlines()

    past_week = datetime.datetime.now() - datetime.timedelta(days=7)
    uid_counter = Counter()

    for log in logs:
        date_str, uid, node_id, result = log.strip().split(',')
        log_date = datetime.datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')

        if log_date >= past_week:
            uid_counter[uid] += 1

    return uid_counter.most_common(100)

# MQTT on_connect callback
def on_connect_edge(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(REQUEST_ACCESS_LIST_TOPIC)
    client.subscribe(AUTHENTICATE_TOPIC)
    client.subscribe(VOTE_RESPONSE_TOPIC)
    client.subscribe(KEY_GENERATION_TOPIC)


# MQTT on_message callback
def on_message_edge(client, userdata, msg):
    global cloud_server_connected, client_cloud, is_generating_keys

    print(f"Message received on topic {msg.topic}: {msg.payload}")
    
    if msg.topic == REQUEST_ACCESS_LIST_TOPIC:
        handle_update_request(msg.payload)
    elif msg.topic == AUTHENTICATE_TOPIC:
        data = json.loads(msg.payload)
        data_authenticate = AuthenticateData(
            encrypted_uid=data["encrypted_uid"],
            node_id=data["node_id"],
            date=datetime.datetime.strptime(data["date"], "%Y-%m-%d %H:%M:%S"),
            result=data["result"],
        )
        process_authentication(data_authenticate)
    elif msg.topic == VOTE_RESPONSE_TOPIC:
        handle_vote_response(json.loads(msg.payload))
    elif msg.topic == KEY_GENERATION_TOPIC:
        seed = msg.payload.decode()
        if not is_generating_keys:
            is_generating_keys = True
            generate_and_publish_keys(seed)

def process_authentication(data: AuthenticateData):
    global access_list, client, client_cloud, cloud_server_connected, private_key
    
    encrypted_uid = data.encrypted_uid
    node_id = data.node_id
    result = data.result
    date = data.date

    new_result = data.result
    
    # Decrypt the UID with the private key to get the original UID
    decrypted_uid = private_key.decrypt(
        bytes.fromhex(encrypted_uid),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode()

    # If negative result, check local access list by comparing decrypted UID with stored UIDs in access_list
    if decrypted_uid in access_list and not result:
        authenticated_info = AuthenticatedData(encrypted_uid=encrypted_uid, result=True, node_id=node_id)
        new_result = True
        client.publish(ALLOW_AUTHENTICATE_TOPIC, json.dumps(authenticated_info.model_dump()))

        print(f"Authenticated {decrypted_uid} at {node_id} on {date}")


    date_str = date.strftime("%Y-%m-%d %H:%M:%S")
    new_data = AuthenticateDataLog(uid=decrypted_uid, node_id=node_id, date=date_str, result=str(new_result))
    write_access_to_file(new_data)

    if cloud_server_connected:
        client_cloud.publish("/nexxgate/access", json.dumps(new_data.model_dump()))
        
# Handle update request
def handle_update_request(payload):
    if payload == b"update":
        update_access_list_from_request()

def update_access_list_from_request():
    global access_list, client
    encrypted_uids = encrypt_uids(access_list)
    public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).hex()
    

    access_list_response = AccessListResponse(access_list=encrypted_uids, public_key=public_key_pem)
    client.publish(RESPONSE_ACCESS_LIST_TOPIC, json.dumps(access_list_response.model_dump()))
[]
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

        # Encrypt UIDs and publish to nodes
        encrypted_uids = encrypt_uids(access_list)

        public_key_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).hex()

        access_list_response = AccessListResponse(access_list=encrypted_uids, public_key=public_key_pem)
        client.publish(ACCESS_LIST_TOPIC, json.dumps(access_list_response.model_dump()))
        print("Access list updated")

    threading.Timer(PERIOD_UPDATE_ACCESS_LIST, update_access_list_schedule).start()



# Update logs to cloud every hour
def update_logs_to_cloud():
    global cloud_server_connected
    print("Sending logs to cloud")

    # If file not found, create it
    try:
        with open(LOG_FILE, "r") as file:
            pass
    except FileNotFoundError:
        with open(LOG_FILE, "w") as file:
            pass

    if cloud_server_connected:
        if api_bridge.upload_log_file(LOG_FILE):
            print("Logs sent to cloud")

            # Clear the logs file
            with open(LOG_FILE, "w") as file:
                pass
        else:
            print("Failed to send logs to cloud")
    threading.Timer(PERIOD_UPDATE_LOGS, update_logs_to_cloud).start()

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

# Start majority vote among edge servers
def start_majority_vote():
    global votes_received, client, access_list
    votes_received = []
    client.publish(MAJORITY_VOTE_TOPIC, json.dumps(encrypt_uids(access_list)))
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

    # Count votes for each access list
    vote_counts = Counter(json.dumps(vote) for vote in votes_received)
    majority_vote = json.loads(vote_counts.most_common(1)[0][0])
    access_list = majority_vote

    encrypted_uids = encrypt_uids(access_list)
    
    public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).hex()

    access_list_response = AccessListResponse(access_list=encrypted_uids, public_key=public_key_pem)
    client.publish(ACCESS_LIST_TOPIC, json.dumps(access_list_response.model_dump()))
    print("Majority vote concluded. Access list updated.")

# Function to hash and encrypt UID
def encrypt_uid(uid):
    global private_key
    # Hash the UID
    digest = hashes.Hash(hashes.SHA256())
    digest.update(uid.encode())
    hashed_uid = digest.finalize()

    # Encrypt the hash using the private key
    encrypted_uid = public_key.encrypt(
        hashed_uid,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return base64.b64encode(encrypted_uid).decode('utf-8')

# Function to encrypt a list of UIDs
def encrypt_uids(uids):
    encrypted_uids = [encrypt_uid(uid) for uid in uids]
    return encrypted_uids

def generate_and_publish_keys(seed):
    global private_key, public_key, is_generating_keys, client, access_list
    private_key, public_key = generate_rsa_key_pair(seed)
    encrypted_uids = encrypt_uids(access_list)
    public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).hex()

    access_list_response = AccessListResponse(access_list=encrypted_uids, public_key=public_key_pem)
    client.publish(ACCESS_LIST_TOPIC, json.dumps(access_list_response.model_dump()))
    print(f"Keys generated and UIDs updated with seed: {seed}")
    is_generating_keys = False

def initiate_key_generation():
    global is_generating_keys, client
    if not is_generating_keys:
        seed = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H')
        client.publish(KEY_GENERATION_TOPIC, seed)
        print(f"Initiated key generation chain with seed: {seed}")
        generate_and_publish_keys(seed)


heartbeat_cloud()  # Start periodic updates
# Wait 5 seconds for the server to start below
time.sleep(5)
update_logs_to_cloud()  # Start periodic updates

# Initialize MQTT Client
client = mqtt.Client(
    client_id=None, userdata=None, protocol=mqtt.MQTTv311, clean_session=True
)
client.on_connect = on_connect_edge
client.on_message = on_message_edge
client.connect(EDGE_MQTT_BROKER, EDGE_MQTT_PORT)
client.loop_start()

# Schedule regular key synchronization and rotation
def sync_encryption_key():
    initiate_key_generation()

def schedule_key_sync():
    while True:
        sync_encryption_key()
        threading.Event().wait(PERIOD_UPDATE_KEYS)  # Check every hour

key_sync_thread = threading.Thread(target=schedule_key_sync)
key_sync_thread.start()

time.sleep(10)
update_access_list_schedule()  # Start periodic updates

# Initialize second MQTT Client for publishing to cloud
client_cloud = mqtt.Client(client_id="", userdata=None, protocol=mqtt.MQTTv5)
client_cloud.tls_set(tls_version=mqtt.ssl.PROTOCOL_TLS)

def on_connect_cloud(client, userdata, flags, rc, properties=None):
    print("Connected to cloud with result code " + str(rc))

client_cloud.on_connect = on_connect_cloud
# Set password and username
client_cloud.username_pw_set("nexxgateuser", "Nexxgate1")
client_cloud.connect("40f10495a5e44f659aa663378f527c6e.s1.eu.hivemq.cloud", 8883)
client_cloud.loop_start()
