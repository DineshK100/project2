# pi_b.py
import paho.mqtt.client as mqtt

BROKER = "172.20.10.2"
TOPIC_SUB = "sensor/pi_a"

def on_message(client, userdata, msg):
    print(f"[Pi B] Got sensor data from Pi A: {msg.payload.decode()}")

client = mqtt.Client(client_id="Pi_B", callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
client.on_message = on_message
client.connect(BROKER, 1883)

client.subscribe(TOPIC_SUB)

print("[Pi B] Listening...")
client.loop_forever()
