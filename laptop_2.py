import paho.mqtt.client as mqtt
from datetime import datetime
from dotenv import load_dotenv
import os 

load_dotenv()

# Configuration
BROKER = os.getenv('MQTT_BROKER')
PORT = int(os.getenv('MQTT_PORT'))

TOPICS = [
    ("lightSensor", 2),
    ("threshold", 2), 
    ("LightStatus", 2),
    ("Status/RaspberryPiA", 2),
    ("Status/RaspberryPiC", 2)
]

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{timestamp()}] Connected to broker")
        
        for topic, qos in TOPICS:
            client.subscribe(topic, qos=qos)
            print(f"[{timestamp()}] Subscribed to '{topic}' (QoS {qos})")
        
        print(f"\n{'='*50}")
        print("MQTT MONITOR - QoS 2")
        print("Tracking LED1 status changes")
        print(f"{'='*50}")
        
    else:
        print(f"Connection failed: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    ts = timestamp()
    
    print(f"\n[{ts}] {topic}: {payload}")
    
    if topic == "LightStatus":
        if payload == "TurnOn":
            print(f"*** LED1 TURNED ON at {ts} ***")
        elif payload == "TurnOff":
            print(f"*** LED1 TURNED OFF at {ts} ***")

client = mqtt.Client(client_id="Monitor", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n[{timestamp()}] Monitor stopped")
    client.disconnect()