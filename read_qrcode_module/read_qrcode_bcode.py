import paho.mqtt.client as mqtt
import time
import configparser
import os
import json
from qr_reader import QRData
from reader_logic import ReaderLogic


CONFIG_FILE = "config.ini"
checkin_checkout_duration = 300
send_interval = 2
message_span = ""
message_expiry_time = 0

# อ่านไฟล์ config.ini
config = configparser.ConfigParser()

try:
    config.read(CONFIG_FILE)
    MQTT_BROKER = config.get("MQTT", "Broker")
    MQTT_PORT = config.getint("MQTT", "Port")
    MQTT_TOPIC = config.get("MQTT", "Topic")
    DEVICE_LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()


client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, client_id=f"scanner-{DEVICE_LOCATION}"
)
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Connected to broker")
except Exception as e:
    print(f"Failed to connect broker: {e}")
    exit()


qr_reader = ReaderLogic(DEVICE_LOCATION, SCAN_COOLDOWN, checkin_checkout_duration)
scan_history = qr_reader.scan_history

try:
    while True:
        current_time = time.time()
        if current_time > message_expiry_time:
            message_span = ""
            token = input()
            if len(token) == 22:
                result = qr_reader.read_qr(token)
                if result["qr_data"]:
                    qr_data = QRData(
                        token, DEVICE_LOCATION, result["status"], int(time.time())
                    )
                    arranged_data = qr_data.write_data()
                    client.publish(MQTT_TOPIC, arranged_data)
                    print(result["message"])
                message_expiry_time = time.time() + send_interval


except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")


client.loop_stop()
client.disconnect()
