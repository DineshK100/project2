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

# Track LED1 state changes
led1_status_log = []

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Include milliseconds

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{timestamp()}] Connected to broker")
        
        for topic, qos in TOPICS:
            client.subscribe(topic, qos=qos)
            print(f"[{timestamp()}] Subscribed to '{topic}' (QoS {qos})")
        
        print(f"\n{'='*70}")
        print("MQTT MONITOR - QoS 2 (Exactly Once Delivery)")
        print("Monitoring all topics and tracking LED1 status changes")
        print(f"{'='*70}\n")
        
    else:
        print(f"Connection failed with return code: {rc}")

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    ts = timestamp()
    
    # Log all messages
    print(f"[{ts}] {topic}: {payload}")
    
    # Track LED1 status changes specifically
    if topic == "LightStatus":
        if payload == "TurnOn":
            led1_status_log.append((ts, "ON"))
            print(f"{'*'*50}")
            print(f"*** LED1 TURNED ON at {ts} ***")
            print(f"{'*'*50}")
        elif payload == "TurnOff":
            led1_status_log.append((ts, "OFF"))
            print(f"{'*'*50}")
            print(f"*** LED1 TURNED OFF at {ts} ***")
            print(f"{'*'*50}")
    
    # Log status changes
    elif "Status/" in topic:
        if payload == "online":
            print(f"    >> {topic.split('/')[-1]} is now ONLINE")
        elif payload == "offline":
            print(f"    >> {topic.split('/')[-1]} is now OFFLINE")

def print_led1_history():
    """Print the complete LED1 status history"""
    print(f"\n{'='*70}")
    print("LED1 STATUS HISTORY (During this session)")
    print(f"{'='*70}")
    if led1_status_log:
        for ts, status in led1_status_log:
            print(f"{ts}: LED1 turned {status}")
    else:
        print("No LED1 status changes recorded yet")
    print(f"{'='*70}\n")

# Create MQTT client
client = mqtt.Client(client_id="Monitor_Laptop2", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"Connecting to broker at {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    
    print("Press Ctrl+C to stop monitoring and see LED1 history summary\n")
    client.loop_forever()
    
except KeyboardInterrupt:
    print(f"\n[{timestamp()}] Monitor stopping...")
    
    # Print LED1 history before exiting
    print_led1_history()
    
    client.disconnect()
    print("Monitor disconnected successfully")
    
except Exception as e:
    print(f"Error: {e}")
    client.disconnect()