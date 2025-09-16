import paho.mqtt.client as mqtt
import time
import configparser
import keyboard
from qr_reader import QR_Data

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
checkin_checkout_toggle = 1  # 1 check-in 0 check-out


# สลับโหมด check-in กับ check-out
def toggle_mode():
    global checkin_checkout_toggle
    checkin_checkout_toggle = 1 - checkin_checkout_toggle


keyboard.add_hotkey("space", toggle_mode)


client = mqtt.Client(callback_api_version=2, client_id=f"scanner-{DEVICE_LOCATION}")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Connected to broker")
except Exception as e:
    print(f"Failed to connect broker: {e}")
    exit()

try:
    while True:
        current_time = time.time()
        if (current_time - last_scan_time) > SCAN_COOLDOWN:
            token = input()
            if token:
                if token != last_token:
                    last_token = token
                    last_scan_time = current_time
                    timestamp = int(current_time)
                    qr_data = QR_Data(
                        token, DEVICE_LOCATION, checkin_checkout_toggle, timestamp
                    )
                    arranged_data = qr_data.get_data()
                    qr_data.write_data()
                    client.publish(MQTT_TOPIC, arranged_data)
                else:
                    # รอ cooldown
                    print("Duplicate token.")
        print(
            "press spacebar to toggle checkin/checkout, press ctrl+c to quit, status",
            checkin_checkout_toggle,
        )
except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")


client.loop_stop()
client.disconnect()
