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

def cleanup_gpio():
    GPIO.cleanup()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("PI B: Connected to broker")
        client.subscribe(LIGHT_STATUS_TOPIC)
        client.subscribe(STATUS_TOPIC_A)
        client.subscribe(STATUS_TOPIC_C)
        print("PI B: Subscribed to all topic")

def on_message(client, userdata, msg):
    global pi_c_online, last_light_status
    
    topic = msg.topic
    payload = msg.payload.decode().strip()
    
    if topic == STATUS_TOPIC_A:
        GPIO.output(LED2_PIN, GPIO.HIGH if payload == "online" else GPIO.LOW)
    
    # Handle Raspberry Pi C status
    elif topic == STATUS_TOPIC_C:
        if payload == "online":
            pi_c_online = True
            GPIO.output(LED3_PIN, GPIO.HIGH)
            # Update LED1 based on current light status
            if last_light_status == "TurnOn":
                GPIO.output(LED1_PIN, GPIO.HIGH)
        elif payload == "offline":
            pi_c_online = False
            GPIO.output(LED3_PIN, GPIO.LOW)
            GPIO.output(LED1_PIN, GPIO.LOW)  # Turn off LED1 when Pi C offline
    
    # Handle light control status
    elif topic == LIGHT_STATUS_TOPIC:
        last_light_status = payload
        # LED1 only works if Pi C is online
        if pi_c_online:
            GPIO.output(LED1_PIN, GPIO.HIGH if payload == "TurnOn" else GPIO.LOW)
        else:
            GPIO.output(LED1_PIN, GPIO.LOW)

setup_gpio()

# MQTT client
client = mqtt.Client(client_id="Pi_B", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, 60)
    client.loop_forever()
    
except KeyboardInterrupt:
    # Turn off all LEDs
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(LED3_PIN, GPIO.LOW)
    
    client.disconnect()
    cleanup_gpio()
    
except Exception as e:
    client.disconnect()
    cleanup_gpio()