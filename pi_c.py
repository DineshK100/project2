import paho.mqtt.client as mqtt
import time
import random
import dotenv
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

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("PI C is connected to broker")
        
        client.publish(STATUS_TOPIC, "online", retain=True) # Need to publish online result 
        print("PI C published online status")
        
        # Subscribe 
        client.subscribe(LIGHT_SENSOR_TOPIC)
        client.subscribe(POTENTIOMETER_TOPIC)
        client.subscribe(LIGHT_STATUS_TOPIC)
        
        print(f"PI C is subscribed to {LIGHT_SENSOR_TOPIC}, {POTENTIOMETER_TOPIC} & {LIGHT_STATUS_TOPIC}")
    else:
        print(f"Pi C Failed to connect, return code {rc}")

def process_decision():
    """Process the light decision based on the threshold"""
    global last_published_decision
    if current_light_value == None or current_threshold_value == None:
        print(f"PI C: Cannot make decision yet, current_light_value: {current_light_value} and current_threshold_value: {current_threshold_value}")
        return
    if current_light_value >= current_threshold_value:
        decision = "TurnOff"
    else:
        decision = "TurnOn"
    
    if decision != last_published_decision: # Publish and Update the light decision
        result = client.publish(LIGHT_STATUS_TOPIC, decision, retain=True)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            last_published_decision = decision
            print(f"Pi C just published decision and it is {decision}")
        else:
            print(f"Pi C failed to publish decision")
        
    else:
        print(f"Pi C: Decision is unchanged")

def on_message(client, userdata, msg):
    global current_light_value, current_threshold_value, last_published_decision
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == LIGHT_SENSOR_TOPIC:
        current_light_value = float(payload)
        process_decision()        
        print(f"PI C: Updated current light value: {current_light_value}")
    elif topic == POTENTIOMETER_TOPIC:
        current_threshold_value = float(payload)
        process_decision()
        print(f"PI C: Updated current threshold value: {current_threshold_value}")
    elif topic == LIGHT_STATUS_TOPIC:
        last_published_decision = payload
        print(f"PI C: Updated last published decision: {last_published_decision}")
        
client = mqtt.Client(client_id="PI_C", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.will_set(STATUS_TOPIC, "offline", retain=True)

client.on_connect = on_connect
client.on_message = on_message

# Connect to broker 
client.connect(BROKER, PORT, 60)

client.loop_start()

print("PI C is now working and will be publishing the values")

try:
    while True:
        time.sleep(1)
        if current_light_value is not None and current_threshold_value is not None:
            current_decision = "TurnOff" if current_light_value >= current_threshold_value else "TurnOn"
            print(f"Current Decision: {current_decision}, current_light_value: {current_light_value:.3f}, curre_threshold_value: {current_threshold_value:.3f}")
        else:
            print(f"Pi C: Waiting for sensor data - Light: {current_light_value}, Threshold: {current_threshold_value}")
        
        time.sleep(9) 
    
except KeyboardInterrupt:
    print("\nPi C Shutting down...")
    
    client.publish(STATUS_TOPIC, "offline", retain=True)
    print(f"Pi C Published status: offline")
    
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
    print("Pi C Disconnected")

except Exception as e:
    print(f"Pi C Error: {e}")
    client.loop_stop()
    client.disconnect()