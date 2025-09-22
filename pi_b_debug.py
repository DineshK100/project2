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
    print("[Pi B] Setting up GPIO pins...")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(LED1_PIN, GPIO.OUT)
    GPIO.setup(LED2_PIN, GPIO.OUT)
    GPIO.setup(LED3_PIN, GPIO.OUT)
    
    # Turn all LEDs off initially
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(LED3_PIN, GPIO.LOW)
    print(f"[Pi B] GPIO setup complete - LED1: Pin {LED1_PIN}, LED2: Pin {LED2_PIN}, LED3: Pin {LED3_PIN}")

def cleanup_gpio():
    print("[Pi B] Cleaning up GPIO...")
    GPIO.cleanup()
    print("[Pi B] GPIO cleanup complete")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[Pi B] Connected to broker at {BROKER}:{PORT}")
        
        client.subscribe(LIGHT_STATUS_TOPIC)
        client.subscribe(STATUS_TOPIC_A)
        client.subscribe(STATUS_TOPIC_C)
        
        print(f"[Pi B] Subscribed to topics:")
        print(f"  - {LIGHT_STATUS_TOPIC}")
        print(f"  - {STATUS_TOPIC_A}")
        print(f"  - {STATUS_TOPIC_C}")
    else:
        print(f"[Pi B] Failed to connect to broker, return code: {rc}")

def on_message(client, userdata, msg):
    global pi_c_online, last_light_status
    
    topic = msg.topic
    payload = msg.payload.decode().strip()
    
    print(f"[Pi B] Received message - Topic: {topic}, Payload: {payload}")
    
    if topic == STATUS_TOPIC_A:
        if payload == "online":
            print("[Pi B] Pi A came online - turning LED2 ON")
            GPIO.output(LED2_PIN, GPIO.HIGH)
        elif payload == "offline":
            print("[Pi B] Pi A went offline - turning LED2 OFF")
            GPIO.output(LED2_PIN, GPIO.LOW)
        else:
            print(f"[Pi B] Unknown Pi A status: {payload}")
    
    # Handle Raspberry Pi C status
    elif topic == STATUS_TOPIC_C:
        if payload == "online":
            print("[Pi B] Pi C came online - turning LED3 ON")
            pi_c_online = True
            GPIO.output(LED3_PIN, GPIO.HIGH)
            
            # Update LED1 based on current light status
            if last_light_status == "TurnOn":
                print("[Pi B] Pi C online + light status TurnOn - turning LED1 ON")
                GPIO.output(LED1_PIN, GPIO.HIGH)
            else:
                print(f"[Pi B] Pi C online but light status is: {last_light_status}")
                
        elif payload == "offline":
            print("[Pi B] Pi C went offline - turning LED3 and LED1 OFF")
            pi_c_online = False
            GPIO.output(LED3_PIN, GPIO.LOW)
            GPIO.output(LED1_PIN, GPIO.LOW)
        else:
            print(f"[Pi B] Unknown Pi C status: {payload}")
    
    # Handle light control status
    elif topic == LIGHT_STATUS_TOPIC:
        print(f"[Pi B] Light status received: {payload}")
        last_light_status = payload
        
        # LED1 only works if Pi C is online
        if pi_c_online:
            if payload == "TurnOn":
                print("[Pi B] Pi C online + TurnOn - turning LED1 ON")
                GPIO.output(LED1_PIN, GPIO.HIGH)
            elif payload == "TurnOff":
                print("[Pi B] Pi C online + TurnOff - turning LED1 OFF")
                GPIO.output(LED1_PIN, GPIO.LOW)
            else:
                print(f"[Pi B] Unknown light command: {payload}")
        else:
            print("[Pi B] Pi C offline - ignoring light status, LED1 stays OFF")
            GPIO.output(LED1_PIN, GPIO.LOW)
    
    else:
        print(f"[Pi B] Received message on unknown topic: {topic}")
    
    # Show current system state
    led1_state = "ON" if GPIO.input(LED1_PIN) else "OFF"
    led2_state = "ON" if GPIO.input(LED2_PIN) else "OFF"  
    led3_state = "ON" if GPIO.input(LED3_PIN) else "OFF"
    
    print(f"[Pi B] Current LED states - LED1: {led1_state}, LED2: {led2_state}, LED3: {led3_state}")
    print(f"[Pi B] System state - Pi C online: {pi_c_online}, Last light status: {last_light_status}")
    print("-" * 60)

print(f"[Pi B] Starting Pi B with broker: {BROKER}:{PORT}")
setup_gpio()

# MQTT client
client = mqtt.Client(client_id="Pi_B", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

print("[Pi B] Connecting to MQTT broker...")

try:
    client.connect(BROKER, PORT, 60)
    print("[Pi B] Starting MQTT loop...")
    client.loop_forever()
    
except KeyboardInterrupt:
    print("\n[Pi B] Keyboard interrupt - shutting down...")
    
    # Turn off all LEDs
    print("[Pi B] Turning off all LEDs...")
    GPIO.output(LED1_PIN, GPIO.LOW)
    GPIO.output(LED2_PIN, GPIO.LOW)
    GPIO.output(LED3_PIN, GPIO.LOW)
    
    client.disconnect()
    cleanup_gpio()
    print("[Pi B] Shutdown complete")
    
except Exception as e:
    print(f"[Pi B] Error occurred: {e}")
    client.disconnect()
    cleanup_gpio()