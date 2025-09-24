import paho.mqtt.client as mqtt
import time
from dotenv import load_dotenv
import os 

load_dotenv()

# Configuration
BROKER = os.getenv('MQTT_BROKER')
PORT = int(os.getenv('MQTT_PORT'))

# Topics
LIGHT_SENSOR_TOPIC = "lightSensor"
POTENTIOMETER_TOPIC = "threshold"
LIGHT_STATUS_TOPIC = "LightStatus"
STATUS_TOPIC = "Status/RaspberryPiC"

# Current Sensor Values 
current_light_value = None
current_threshold_value = None
last_published_decision = None
pending_decision_publish = None

def on_connect(client, userdata, flags, rc):
    global last_published_decision
    if rc == 0:
        print("PI C is connected to broker")
        
        client.publish(STATUS_TOPIC, "online", retain=True, qos=2)
        print("PI C published online status")
        
        client.subscribe(LIGHT_SENSOR_TOPIC, qos=2)
        client.subscribe(POTENTIOMETER_TOPIC, qos=2)
        client.subscribe(LIGHT_STATUS_TOPIC, qos=2)
        
        print(f"PI C is subscribed to {LIGHT_SENSOR_TOPIC}, {POTENTIOMETER_TOPIC} & {LIGHT_STATUS_TOPIC}")
        
        last_published_decision = None
    else:
        print(f"Pi C Failed to connect, return code {rc}")

def process_decision():
    global last_published_decision, pending_decision_publish
    
    if current_light_value is None or current_threshold_value is None:
        print(f"PI C: Cannot make decision yet, light: {current_light_value}, threshold: {current_threshold_value}")
        return
    
    # Determine decision based on light vs threshold
    if current_light_value >= current_threshold_value:
        decision = "TurnOff"  # More light = turn off
    else:
        decision = "TurnOn"   # Less light = turn on
    
    # Check if we need to publish
    should_publish = False
    
    if last_published_decision is None:
        should_publish = True
        print(f"PI C: Initial decision needed")
    elif decision != last_published_decision:
        should_publish = True
        print(f"PI C: Decision changed from {last_published_decision} to {decision}")
    elif pending_decision_publish is not None and decision != pending_decision_publish:
        should_publish = True
        print(f"PI C: Decision differs from pending")
    
    if should_publish:
        pending_decision_publish = decision
        result = client.publish(LIGHT_STATUS_TOPIC, decision, qos=2, retain=True)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"PI C published decision: {decision} (Light: {current_light_value:.3f}, Threshold: {current_threshold_value:.3f})")
        else:
            print(f"PI C failed to publish decision")
            pending_decision_publish = None
    else:
        print(f"PI C: Decision unchanged: {decision}")

def on_message(client, userdata, msg):
    global current_light_value, current_threshold_value, last_published_decision, pending_decision_publish
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == LIGHT_SENSOR_TOPIC:
        new_value = float(payload)
        if current_light_value != new_value:
            current_light_value = new_value
            print(f"PI C: Updated light value: {current_light_value:.3f}")
            process_decision()
    elif topic == POTENTIOMETER_TOPIC:
        new_value = float(payload)
        if current_threshold_value != new_value:
            current_threshold_value = new_value
            print(f"PI C: Updated threshold value: {current_threshold_value:.3f}")
            process_decision()
    elif topic == LIGHT_STATUS_TOPIC:
        # Verify this matches what we were expecting
        if pending_decision_publish is None or payload == pending_decision_publish:
            last_published_decision = payload
            pending_decision_publish = None
            print(f"PI C: Confirmed last published decision: {last_published_decision}")

client = mqtt.Client(client_id="PI_C", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

client.will_set(STATUS_TOPIC, "offline", qos=2, retain=True)

client.on_connect = on_connect
client.on_message = on_message

print(f"PI C: Connecting to broker at {BROKER}...")
client.connect(BROKER, PORT, 60)

client.loop_start()

print("PI C is now work")

try:
    while True:
        time.sleep(1)
        if current_light_value is not None and current_threshold_value is not None:
            current_decision = "TurnOff" if current_light_value >= current_threshold_value else "TurnOn"
            status = "ON" if current_decision == "TurnOn" else "OFF"
            print(f"PI C Status: LED should be {status} | Light: {current_light_value:.3f}, Threshold: {current_threshold_value:.3f}")
        else:
            print(f"PI C: Waiting for sensor data - Light: {current_light_value}, Threshold: {current_threshold_value}")
        
        time.sleep(9)  # Total 10 second loop
    
except KeyboardInterrupt:
    print("\nPI C: Shutting down gracefully...")
    
    client.publish(STATUS_TOPIC, "offline", qos=2, retain=True)
    print(f"PI C: Published status: offline")
    
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
    print("PI C: Disconnected")

except Exception as e:
    print(f"PI C Error: {e}")
    client.loop_stop()
    client.disconnect()