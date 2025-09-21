#!/usr/bin/env python3
# pi_a.py - Simple MQTT test for Pi A
import paho.mqtt.client as mqtt
import time
import random

BROKER = "172.20.10.2" 
TOPIC_PUB = "sensor/pi_a"
TOPIC_SUB = "led/pi_a"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[Pi A] Connected to broker!")
        client.subscribe(TOPIC_SUB)
        print(f"[Pi A] Subscribed to {TOPIC_SUB}")
    else:
        print(f"[Pi A] Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    print(f"[Pi A] Received on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client(client_id="Pi_A", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_connect = on_connect
client.on_message = on_message

print(f"[Pi A] Connecting to broker at {BROKER}...")
client.connect(BROKER, 1883, 60)

client.loop_start()

try:
    while True:
        sensor_value = random.randint(0, 1023)
        result = client.publish(TOPIC_PUB, sensor_value)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"[Pi A] Published sensor value: {sensor_value}")
        else:
            print(f"[Pi A] Failed to publish")
            
        time.sleep(2)
        
except KeyboardInterrupt:
    print("\n[Pi A] Shutting down...")
    client.loop_stop()
    client.disconnect()
    print("[Pi A] Disconnected")