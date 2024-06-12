# Responses to the frontend and backend
from pydantic import BaseModel
import requests

# Cloud Server API URL
api_cloud = "https://nexxgate-backend.onrender.com/nexxgate/api/v1/"
# API Key for the Edge Server (unique per Edge Server)
API_KEY = "aj1jD9mf11"


class AccessListResponseItem(BaseModel):
    """
    Represents an item in the access list response.

    Attributes:
        uid (str): The unique identifier of the item.
    """

    uid: str


def check_cloud_connection() -> bool:
    """
    Check the connection to the Cloud Server.

    Returns:
        bool: True if the connection is successful, False otherwise.
    """
    try:
        response = requests.get(api_cloud + "health-check/", timeout=10)
        if response.status_code == 200:
            cloud_server_connected = True
        else:
            cloud_server_connected = False
    except Exception as e:
        print(f"Failed to connect to the Cloud Server. Error: {e}")
        cloud_server_connected = False
        return cloud_server_connected
    finally:
        return cloud_server_connected


# Send a heartbeat to the Cloud Server
def send_edge_heartbeat() -> bool:
    """
    Sends a heartbeat to the cloud API to indicate that the edge server is active.

    Returns:
        bool: True if the heartbeat was successfully sent (status code 200), False otherwise.
    """
    try:
        response = requests.get(api_cloud + "edge_heartbeat/" + API_KEY, timeout=10)
        if response.status_code == 200:
            return True
        return False
    except Exception as e:
        print(f"Failed to send heartbeat. Error: {e}")
        return False


# Get updated access list from the Cloud Server
def get_updated_access_list() -> list[AccessListResponseItem]:
    """
    Retrieves the updated access list from the API cloud.

    Returns:
        A list of AccessListResponseItem objects representing the updated access list.
        Returns None if there was an error retrieving the access list.
    """
    try:
        response = requests.get(api_cloud + "access_list/", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Failed to get updated access list. Error: {e}")
        return None


# Send access logs to the Cloud Server from the file access_log.txt
def upload_log_file(file_path: str) -> bool:
    """
    Uploads a log file to the API cloud server.

    Args:
        file_path (str): The path to the log file.

    Returns:
        bool: True if the log file was uploaded successfully, False otherwise.
    """
    try:
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(api_cloud + "upload-log/", files=files, timeout=10)

        if response.status_code == 201:
            print("Logs uploaded successfully")
            return True
        else:
            print(f"Failed to upload logs. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Failed to upload logs. Error: {e}")
        return False
