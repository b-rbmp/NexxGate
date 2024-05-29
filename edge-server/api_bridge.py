# Responses to the frontend and backend
from pydantic import BaseModel
import requests

api_cloud = "http://127.0.0.1:8000/nexxgate/api/v1/"
api_key = "aj1jD9mf11"

class AccessListResponseItem(BaseModel):
    uid: str
    # biometric_data: str

# Check if the Cloud Server is connected
def check_cloud_connection() -> bool:
    response = requests.get(api_cloud + "health-check/")
    if response.status_code == 200:
        cloud_server_connected = True
    else:
        cloud_server_connected = False

    return cloud_server_connected

# Send a heartbeat to the Cloud Server
def send_edge_heartbeat() -> bool:
    response = requests.get(api_cloud + "edge_heartbeat/" + api_key)
    if response.status_code == 200:
        return True
    return False

# Get updated access list from the Cloud Server
def get_updated_access_list() -> list[AccessListResponseItem]:
    response = requests.get(api_cloud + "access-list/")
    if response.status_code == 200:
        return response.json()  
    return None

# Send access logs to the Cloud Server from the file access_log.txt
def upload_log_file(file_path: str) -> bool:
    with open(file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(api_cloud + "upload-log/", files=files)
    
    if response.status_code == 201:
        print("Logs uploaded successfully")
        return True
    else:
        print(f"Failed to upload logs. Status code: {response.status_code}")
        return False