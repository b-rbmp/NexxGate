
import datetime
import json
import paho.mqtt.client as paho
from paho import mqtt
from sqlalchemy.orm import Session
from app import models, schemas
from app.dependencies import get_db_standalone
from config import settings

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Callback function triggered when the client successfully connects to the MQTT broker.

    Parameters:
        client: The MQTT client instance.
        userdata: The user data associated with the client.
        flags: The flags associated with the connection.
        rc: The connection result code.
        properties: The properties associated with the connection (optional).

    Returns:
        None
    """
    print("CONNACK received with code %s." % rc)


def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    """
    Callback function triggered when a subscription is successful.

    Args:
        client: The MQTT client instance.
        userdata: The user data associated with the client.
        mid: The message ID of the subscription.
        granted_qos: The list of QoS levels granted for the subscription.
        properties: The optional properties associated with the subscription.

    Returns:
        None
    """
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_message(client, userdata, msg):
    """
    Callback function that is called when a message is received.

    Args:
        client: The MQTT client instance that received the message.
        userdata: Any user-defined data that was passed to the MQTT client.
        msg: The received message object.

    Returns:
        None
    """
    topic: str = msg.topic
    if topic.startswith("/nexxgate/access"):
        print("Received message: " + str(msg.payload))
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        try:
            # Model Received message: b'{"uid": "12345", "node_id": "A5EF1877", "date": "2021-09-01 12:00:00", "result": true. "api_key": "jd99ada"}'

            # Decode the incoming message above instead of the one below
            m_in=json.loads(m_decode) #decode json data
            if "uid" not in m_in:
                print("No uid key")
            elif "node_id" not in m_in:
                print("No node_id key")
            elif "result" not in m_in:
                print("No result key")
            elif "date" not in m_in:
                print("No date key")
            elif "api_key" not in m_in:
                print("No api_key key")
            else:
                try:
                    # Get a database connection
                    db: Session = get_db_standalone()
                    
                    # Validate incoming data
                    data = schemas.AuthenticateData(
                        uid=m_in['uid'],
                        node_id=m_in['node_id'],
                        date=datetime.datetime.strptime(m_in['date'], "%Y-%m-%d %H:%M:%S"),
                        result=m_in['result'],
                        api_key=m_in['api_key']
                    )
                    
                    # Get edge server by api_key
                    edge_server = db.query(models.EdgeServer).filter(models.EdgeServer.api_key == data.api_key).first()
                    if edge_server is None:
                        print("No edge server found")
                        return
                    
                    # Log every authentication attempt
                    access_log = schemas.AccessLogCreateIn(
                        device_node_id=data.node_id,
                        timestamp=data.date,
                        uid=data.uid,
                        granted=data.result,
                        edge_server_id=edge_server.id
                    )

                    # Save the access log
                    access_log = models.AccessLog(**access_log.model_dump())
                    db.add(access_log)
                    db.commit()
                    
                except Exception as e:
                    print("Error: " + e)
                finally:
                    db.close()
        except Exception as e:
            print("Error: " + e)
        

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
if settings.MQTT_SSL:
    client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect(settings.MQTT_HOST, settings.MQTT_PORT)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("#", qos=0)

