import paho.mqtt.client as mqtt
import time
import configparser

# อ่านไฟล์ config.ini
config = configparser.ConfigParser()
try:
    config.read("config.ini")
    MQTT_BROKER = config.get("MQTT", "Broker")
    MQTT_PORT = config.getint("MQTT", "Port")
    MQTT_TOPIC = config.get("MQTT", "Topic")
    LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
    READER_SIZE = config.getint("Device", "ReaderSize")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()

last_token = None
last_scan_time = 0

client = mqtt.Client(callback_api_version=2, client_id=f"scanner-{LOCATION}")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Connected to broker")
except Exception as e:
    print(f"Failed to connect broker: {e}")
    exit()

while True:
    token = input()
    if token:
        current_time = time.time()
        if token != last_token or (current_time - last_scan_time) > SCAN_COOLDOWN:
            last_token = token
            last_scan_time = current_time
            timestamps = int(current_time)
            raw_data = f"{token},{timestamps}, {LOCATION}"
            print(f"Token: {token}, Time: {timestamps}, Location: {LOCATION}")
            client.publish(MQTT_TOPIC, raw_data)
        else:
            # รอ cooldown
            print("Duplicate token.")

client.loop_stop()
client.disconnect()
