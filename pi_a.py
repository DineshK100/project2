# pi_a.py
import paho.mqtt.client as mqtt
import time
import random  # placeholder for sensor data

BROKER = "172.16.14.113"  # IP of Laptop #1 (your broker)
TOPIC_PUB = "sensor/pi_a"
TOPIC_SUB = "led/pi_a"

# Callback when message is received
def on_message(client, userdata, msg):
    print(f"[Pi A] Received on {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client("Pi_A")
client.on_message = on_message
client.connect(BROKER, 1883)

# Subscribe to LED control topic
client.subscribe(TOPIC_SUB)

client.loop_start()

try:
    while True:
        sensor_value = random.randint(0, 1023)
        client.publish(TOPIC_PUB, sensor_value)
        print(f"[Pi A] Published sensor value: {sensor_value}")
        time.sleep(2)
except KeyboardInterrupt:
    client.loop_stop()
    client.disconnect()
