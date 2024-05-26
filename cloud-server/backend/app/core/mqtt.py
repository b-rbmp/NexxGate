
import datetime
import json
import paho.mqtt.client as paho
from paho import mqtt
from sqlalchemy.orm import Session
from app import schemas
from app.dependencies import get_db_standalone
from config import settings

# setting callbacks for different events to see if it works, print the message etc.
def on_connect(client, userdata, flags, rc, properties=None):
    print("CONNACK received with code %s." % rc)


# print which topic was subscribed to
def on_subscribe(client, userdata, mid, granted_qos, properties=None):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

# print message, useful for checking if it was successful
def on_message(client, userdata, msg):

    topic: str = msg.topic
    if topic.startswith("nexxgate/access"):
        m_decode=str(msg.payload.decode("utf-8","ignore"))
        m_in=json.loads(m_decode) #decode json data
        if "uid" not in m_in:
            print("No uid key")
        elif "node_id" not in m_in:
            print("No node_id key")
        elif "result" not in m_in:
            print("No result key")
        elif "date" not in m_in:
            print("No date key")
        else:
            try:
                db: Session = get_db_standalone()
                
                # Validate incoming data
                data = schemas.AuthenticateData(
                    uid=m_in['uid'],
                    node_id=m_in['node_id'],
                    date=datetime.datetime.strptime(m_in['date'], "%Y-%m-%d %H:%M:%S"),
                    result=m_in['result']
                )

                # Log every authentication attempt
                access_log = schemas.AccessLogCreateIn(
                    device_node_id=data.node_id,
                    timestamp=data.date,
                    uid=data.uid,
                    granted=data.result
                )
                db.add(access_log)
                db.commit()
                
            except Exception as e:
                print("Error: " + e)
            finally:
                db.close()

# using MQTT version 5 here, for 3.1.1: MQTTv311, 3.1: MQTTv31
# userdata is user defined data of any type, updated by user_data_set()
# client_id is the given name of the client
client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
client.on_connect = on_connect

# enable TLS for secure connection
#client.tls_set(tls_version=mqtt.client.ssl.PROTOCOL_TLS)
# set username and password
#client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASS)
# connect to HiveMQ Cloud on port 8883 (default for MQTT)
client.connect(settings.MQTT_HOST, settings.MQTT_PORT)

# setting callbacks, use separate functions like above for better visibility
client.on_subscribe = on_subscribe
client.on_message = on_message

# subscribe to all topics of encyclopedia by using the wildcard "#"
client.subscribe("nexxgate/#", qos=0)