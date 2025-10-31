import paho.mqtt.client as mqtt
import json
import time
from Adafruit_IO import MQTTClient

# -------------------------------
# Adafruit IO Setup
# -------------------------------
AIO_USERNAME = "thunder_69"
AIO_KEY = "YOUR_ADAFRUIT_IO_KEY"
aio_client = MQTTClient(AIO_USERNAME, AIO_KEY)
aio_client.connect()
aio_client.loop_background()

# -------------------------------
# Local MQTT Setup
# -------------------------------
energy = {"node1": 0.0, "node2": 0.0}
last_time = time.time()

device_topics = {
    "node1": "ems/node1/data",
    "node2": "ems/node2/data"
}

control_topics = {
    "node1": "ems/node1/control",
    "node2": "ems/node2/control"
}

MAX_VOLTAGE = 245.0
MAX_CURRENT = 2.0  # Amps

# -------------------------------
# Message Handler
# -------------------------------
def on_message(client, userdata, msg):
    global last_time
    now = time.time()
    dt = (now - last_time) / 3600.0
    last_time = now

    data = json.loads(msg.payload.decode())

    if msg.topic.endswith("node1/data"):
        device = "node1"
    elif msg.topic.endswith("node2/data"):
        device = "node2"
    else:
        return

    voltage = data["voltage"]
    current = data["current"]
    power = voltage * current
    energy[device] += power * dt / 1000.0  # Wh → kWh

    print(f"{device} | V: {voltage:.1f}V | I: {current:.4f}A | P: {power:.3f}W | E: {energy[device]:.4f}kWh")

    # Publish to Adafruit IO
    aio_client.publish(f"{device}_power", power)
    aio_client.publish("total_energy", energy["node1"] + energy["node2"])

    # Control logic
    if voltage > MAX_VOLTAGE or current > MAX_CURRENT:
        print(f"⚠️ {device} anomaly detected! Relay OFF")
        client.publish(control_topics[device], "OFF")
    else:
        client.publish(control_topics[device], "ON")

# -------------------------------
# MQTT Broker Setup
# -------------------------------
client = mqtt.Client()
client.on_message = on_message
client.connect("localhost", 1883)

for topic in device_topics.values():
    client.subscribe(topic)

print("✅ Edge Device Running... Data will appear on Adafruit IO Dashboard.")
client.loop_forever()
