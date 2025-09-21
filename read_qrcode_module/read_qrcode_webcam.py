import cv2
import paho.mqtt.client as mqtt
import time
import configparser
import os
import json
from qr_reader import QR_Data
from camera import Camera

CONFIG_FILE = "config.ini"
CV2_FRAME = "QR Code Scanner"
RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (255, 0, 0)
YELLOW_COLOR = (255, 255, 0)
WHITE_COLOR = (255, 255, 255)
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
    LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
    READER_SIZE = config.getint("Device", "ReaderSize")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"scanner-{LOCATION}")
try:
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    print("Connected to broker")
except Exception as e:
    print(f"Failed to connect broker: {e}")
    exit()


def drawText(frame, x, y, text, color=GREEN_COLOR):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


def load_data():
    if not os.path.exists("qr_log.json") or os.path.getsize("qr_log.json") == 0:
        print("QR Log created")
        return {}
    try:
        with open("qr_log.json", "r", encoding="UTF-8") as log_file:
            history = {}
            all_logs = json.load(log_file)
            for log in reversed(all_logs):
                token = log.get("token")
                timestamp = log.get("timestamp")
                if token and timestamp and token not in history:
                    if log.get("status") == 1:
                        history[token] = timestamp
    except Exception as e:
        print(f"Log file error: {e}")
    return history


cap = Camera()
qr = cv2.QRCodeDetector()

scan_history = load_data()

cv2.namedWindow(CV2_FRAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(CV2_FRAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        ret, frame = cap.get_frame()
        if not ret:
            continue
        if (
            cv2.waitKey(1) & 0xFF == ord("q")
            or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1
        ):
            print("QR Code Reading is shutting down.")
            exit()

        # กำหนดขนาดและตำแหน่งของพื้นที่สแกน QR Code
        frame_h, frame_w, _ = frame.shape
        roi_x = int((frame_w - READER_SIZE) / 2)
        roi_y = int((frame_h - READER_SIZE) / 2)

        current_time = time.time()
        if current_time > message_expiry_time:
            message_span = ""
            reader_frame = frame[
                roi_y : roi_y + READER_SIZE, roi_x : roi_x + READER_SIZE
            ]
            roi_frame = frame[roi_y : roi_y + READER_SIZE, roi_x : roi_x + READER_SIZE]
            token, points, _ = qr.detectAndDecode(roi_frame)
            if points is not None and cv2.contourArea(points) > 0 and len(token) == 22:
                timestamp = int(current_time)
                status = -1
                qr_data = QR_Data(token, LOCATION, status, timestamp)
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
                    qr_data.write_data()
                    print(scan_history)
                    client.publish(MQTT_TOPIC, arranged_data)
                    time.sleep(send_interval)

        if message_span:
            drawText(frame, roi_x, roi_y - 10, message_span, WHITE_COLOR)
        else:
            drawText(frame, roi_x, roi_y - 10, "Place QR Code here", BLUE_COLOR)
        cv2.rectangle(
            frame,
            (roi_x, roi_y),
            (roi_x + READER_SIZE, roi_y + READER_SIZE),
            (255, 255, 255),
            3,
        )
        cv2.imshow(CV2_FRAME, frame)

except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")
cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
