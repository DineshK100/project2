import paho.mqtt.client as mqtt
import time
import RPi.GPIO as GPIO
from dotenv import load_dotenv
import os 

load_dotenv()

# Configuration
BROKER = os.getenv('MQTT_BROKER')
PORT = int(os.getenv('MQTT_PORT'))

LIGHT_STATUS_TOPIC = "LightStatus"
STATUS_TOPIC_A = "Status/RaspberryPiA"
STATUS_TOPIC_C = "Status/RaspberryPiC"

# GPIO Pin assignments
LED1_PIN = 17  # Light control LED
LED2_PIN = 27  # Pi A status LED  
LED3_PIN = 22  # Pi C status LED

# State tracking
pi_c_online = False
last_light_status = None

def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)
    GPIO.setup(LED3_PIN, GPIO.OUT)
    
    # Turn all LEDs off initially
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(LED3_PIN, GPIO.LOW)
    print("PI B: All LEDs initialized to OFF")

def cleanup_gpio():
    GPIO.cleanup()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("PI B: Connected to broker")
        # Subscribe with QoS 2
        client.subscribe(LIGHT_STATUS_TOPIC, qos=2)
        client.subscribe(STATUS_TOPIC_A, qos=2)
        client.subscribe(STATUS_TOPIC_C, qos=2)
        print("PI B: Subscribed to all topics with QoS 2")
    else:
        print(f"PI B: Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global pi_c_online, last_light_status
    
    topic = msg.topic
    payload = msg.payload.decode().strip()
    
    print(f"PI B Received: {topic} = {payload}")
    
    if topic == STATUS_TOPIC_A:
        if payload == "online":
            GPIO.output(LED2_PIN, GPIO.HIGH)
            print("PI B: LED2 ON (Pi A online)")
        else:
            GPIO.output(LED2_PIN, GPIO.LOW)
            print("PI B: LED2 OFF (Pi A offline)")
    
    # Handle Raspberry Pi C status
    elif topic == STATUS_TOPIC_C:
        if payload == "online":
            pi_c_online = True
            GPIO.output(LED3_PIN, GPIO.HIGH)
            print("PI B: LED3 ON (Pi C online)")
            # Update LED1 based on current light status
            if last_light_status == "TurnOn":
                GPIO.output(LED1_PIN, GPIO.HIGH)
                print("PI B: LED1 ON (Pi C online and light should be on)")
            elif last_light_status == "TurnOff":
                GPIO.output(LED1_PIN, GPIO.LOW)
                print("PI B: LED1 OFF (Pi C online but light should be off)")
        elif payload == "offline":
            pi_c_online = False
            GPIO.output(LED3_PIN, GPIO.LOW)
            GPIO.output(LED1_PIN, GPIO.LOW)  # Turn off LED1 when Pi C offline
            print("PI B: LED3 OFF, LED1 OFF (Pi C offline)")
    
    # Handle light control status
    elif topic == LIGHT_STATUS_TOPIC:
        last_light_status = payload
        # LED1 only works if Pi C is online
        if pi_c_online:
            if payload == "TurnOn":
                GPIO.output(LED1_PIN, GPIO.HIGH)
                print("PI B: LED1 ON (Light status: TurnOn)")
            else:
                GPIO.output(LED1_PIN, GPIO.LOW)
                print("PI B: LED1 OFF (Light status: TurnOff)")
        else:
            GPIO.output(LED1_PIN, GPIO.LOW)
            print("PI B: LED1 remains OFF (Pi C offline)")

setup_gpio()

# MQTT client
client = mqtt.Client(client_id="Pi_B", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"PI B: Connecting to broker at {BROKER}...")
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
    
except KeyboardInterrupt:
    print("\nPI B: Shutting down...")
    # Turn off all LEDs
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(LED3_PIN, GPIO.LOW)
    print("PI B: All LEDs turned OFF")
    
    client.disconnect()
    cleanup_gpio()
    print("PI B: Disconnected and cleaned up")
    
except Exception as e:
    print(f"PI B Error: {e}")
    client.disconnect()
    cleanup_gpio()