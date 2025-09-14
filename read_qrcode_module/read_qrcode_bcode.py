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
    DEVICE_LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()

last_token = None
last_scan_time = 0

client = mqtt.Client(callback_api_version=2, client_id=f"scanner-{DEVICE_LOCATION}")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Connected to broker")
except Exception as e:
    print(f"Failed to connect broker: {e}")
    exit()

while True:
    current_time = time.time()
    if (current_time - last_scan_time) > SCAN_COOLDOWN:
        token = input()
        if token:
            if token != last_token:
                last_token = token
                last_scan_time = current_time
                timestamps = int(current_time)
                raw_data = f"{token},{timestamps}, {DEVICE_LOCATION}"
                print(
                    f"Token: {token}, Time: {timestamps}, DEVICE_Location: {DEVICE_LOCATION}"
                )
                client.publish(MQTT_TOPIC, raw_data)
            else:
                # รอ cooldown
                print("Duplicate token.")

client.loop_stop()
client.disconnect()
