import paho.mqtt.client as mqtt
import time
import configparser
from qr_reader import QR_Data

CONFIG_FILE = "config.ini"
scan_history = {}
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

try:
    while True:
        current_time = time.time()
        if current_time > message_expiry_time:
            message_span = ""
            token = input()
            if len(token) == 22:
                timestamp = int(current_time)
                status = -1
                qr_data = QR_Data(token, DEVICE_LOCATION, status, timestamp)
                if token in scan_history:
                    last_scan_time = scan_history[token]
                    time_diff = current_time - last_scan_time
                    if time_diff < SCAN_COOLDOWN:
                        message_span = "Wait..."
                    elif time_diff > checkin_checkout_duration:
                        status = 0
                        del scan_history[token]
                        message_span = "Checked out"
                    else:
                        status = 1
                        scan_history[token] = current_time
                        message_span = "Rechecked in"
                else:
                    status = 1
                    scan_history[token] = current_time
                    message_span = "Checked in"

                if status >= 0:
                    qr_data.set_status(status)
                    arranged_data = qr_data.get_data()
                    print(qr_data.get_data())
                    print(scan_history)
                    client.publish(MQTT_TOPIC, arranged_data)
                    time.sleep(send_interval)

except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")


client.loop_stop()
client.disconnect()
