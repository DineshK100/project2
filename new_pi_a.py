import paho.mqtt.client as mqtt
import time
import spidev
from dotenv import load_dotenv
import os 

load_dotenv()

# Configuration
BROKER = os.getenv('MQTT_BROKER')
PORT = int(os.getenv('MQTT_PORT'))

LIGHT_SENSOR_TOPIC = "lightSensor"
POTENTIOMETER_TOPIC = "threshold"
STATUS_TOPIC = "Status/RaspberryPiA"

LDR_THRESHOLD = 5  
POTENTIOMETER_THRESHOLD = 5

# SPI configuration for MCP3008 ADC
spi = spidev.SpiDev()
spi.open(0, 0)  # Bus 0, Device 0
spi.max_speed_hz = 1000000

# ADC channel assignments
LDR_CHANNEL = 0         # Channel 0 for LDR
POTENTIOMETER_CHANNEL = 1  # Channel 1 for potentiometer

# ADC reading parameters (adjust based on your actual readings)
LDR_MIN = 10    # Minimum LDR ADC value (no light)
LDR_MAX = 100   # Maximum LDR ADC value (bright light)
POT_MIN = 90    # Minimum potentiometer ADC value
POT_MAX = 250   # Maximum potentiometer ADC value

# Storing the last published values for ldr and potentiometer
last_published_ldr = None
last_published_pot = None

# Track what we're about to publish to prevent duplicates
pending_ldr_publish = None
pending_pot_publish = None

def read_adc(channel):
    """Read analog value from MCP3008 ADC channel"""
    # MCP3008 command format: start bit + single/diff + channel bits
    command = [1, (8 + channel) << 4, 0]
    adc_response = spi.xfer2(command)
    
    # Extract 10-bit ADC value from response
    adc_value = ((adc_response[1] & 3) << 8) + adc_response[2]
    return adc_value

def read_ldr():
    """Read LDR value from ADC"""
    return read_adc(LDR_CHANNEL)

def read_potentiometer():
    """Read potentiometer value from ADC"""
    return read_adc(POTENTIOMETER_CHANNEL)

def on_connect(client, userdata, flags, rc):
    global last_published_ldr, last_published_pot
    if rc == 0:
        print("PI A is connected to broker")
        
        client.publish(STATUS_TOPIC, "online", retain=True, qos=2)
        print("PI A published online status")
        
        # Subscribe with QoS 2
        client.subscribe(LIGHT_SENSOR_TOPIC, qos=2)
        client.subscribe(POTENTIOMETER_TOPIC, qos=2)
        print(f"PI A is subscribed to {LIGHT_SENSOR_TOPIC} & {POTENTIOMETER_TOPIC}")
        
        # Reset last published values on reconnect to get retained messages
        last_published_ldr = None
        last_published_pot = None
    else:
        print(f"[Pi A] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global last_published_ldr, last_published_pot, pending_ldr_publish, pending_pot_publish
    
    topic = msg.topic
    payload = msg.payload.decode()
    
    if topic == LIGHT_SENSOR_TOPIC:
        value = float(payload)
        # Only update if this isn't a duplicate from our pending publish
        if pending_ldr_publish is None or abs(value - pending_ldr_publish) < 0.001:
            last_published_ldr = value
            pending_ldr_publish = None
            print(f"PI A Updated last published LDR value: {last_published_ldr}")
    elif topic == POTENTIOMETER_TOPIC:
        value = float(payload)
        # Only update if this isn't a duplicate from our pending publish
        if pending_pot_publish is None or abs(value - pending_pot_publish) < 0.001:
            last_published_pot = value
            pending_pot_publish = None
            print(f"PI A Updated last published POT value: {last_published_pot}")

def normalize_value(value, min_val, max_val):
    """Normalize the value between 0 - 1"""
    normalized = (value - min_val) / (max_val - min_val)
    return max(0.0, min(1.0, normalized))

def should_publish_ldr(current_normalized):
    if last_published_ldr is None:
        return True 
    # Check against both last published and pending values
    if pending_ldr_publish is not None:
        return abs(current_normalized - pending_ldr_publish) > (LDR_THRESHOLD / 100.0)
    return abs(current_normalized - last_published_ldr) > (LDR_THRESHOLD / 100.0)

def should_publish_pot(current_normalized):
    if last_published_pot is None:
        return True 
    # Check against both last published and pending values
    if pending_pot_publish is not None:
        return abs(current_normalized - pending_pot_publish) > (POTENTIOMETER_THRESHOLD / 100.0)
    return abs(current_normalized - last_published_pot) > (POTENTIOMETER_THRESHOLD / 100.0)

# Creation of MQTT Client Object
client = mqtt.Client(client_id="PI_A", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)

# Will message sent to the broker if disconnects unexpectedly - QoS 2
client.will_set(STATUS_TOPIC, "offline", qos=2, retain=True)

client.on_connect = on_connect
client.on_message = on_message

print(f"[Pi A] Connecting to broker at {BROKER}...")
client.connect(BROKER, PORT, 60)

# Creates thread to ensure network stuff is happening in the background
client.loop_start()

try:
    while True:
        ldr_raw = read_ldr()
        pot_raw = read_potentiometer()

        ldr_normalized = normalize_value(ldr_raw, LDR_MIN, LDR_MAX)
        pot_normalized = normalize_value(pot_raw, POT_MIN, POT_MAX)
        
        publish_ldr = should_publish_ldr(ldr_normalized)
        publish_pot = should_publish_pot(pot_normalized)
        
        if publish_ldr or publish_pot:
            print(f"Pi A publishing sensor data")
            
            if publish_ldr:
                # Track what we're about to publish
                pending_ldr_publish = ldr_normalized
                result_ldr = client.publish(LIGHT_SENSOR_TOPIC, f"{ldr_normalized:.3f}", qos=2, retain=True)
                if result_ldr.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"[Pi A] Published LDR: {ldr_normalized:.3f} (raw: {ldr_raw}) - RETAINED")
                else:
                    print(f"[Pi A] Failed to publish LDR value")
                    pending_ldr_publish = None
            
            if publish_pot:
                # Track what we're about to publish
                pending_pot_publish = pot_normalized
                result_pot = client.publish(POTENTIOMETER_TOPIC, f"{pot_normalized:.3f}", qos=2, retain=True)
                if result_pot.rc == mqtt.MQTT_ERR_SUCCESS:
                    print(f"[Pi A] Published Potentiometer: {pot_normalized:.3f} (raw: {pot_raw}) - RETAINED")
                else:
                    print(f"[Pi A] Failed to publish potentiometer value")
                    pending_pot_publish = None
        
        time.sleep(0.1)  # Sample every 100ms
        
except KeyboardInterrupt:
    print("\n[Pi A] Shutting down gracefully...")
    
    client.publish(STATUS_TOPIC, "offline", qos=2, retain=True)
    print(f"[Pi A] Published status: offline")
    
    time.sleep(0.5)
    client.loop_stop()
    client.disconnect()
    spi.close()  # Close SPI connection
    print("[Pi A] Disconnected")
    
except Exception as e:
    print(f"[Pi A] Error: {e}")
    client.loop_stop()
    client.disconnect()
    spi.close()  # Close SPI connection