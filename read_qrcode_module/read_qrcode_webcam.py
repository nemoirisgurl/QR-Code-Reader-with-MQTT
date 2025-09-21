import cv2
import paho.mqtt.client as mqtt
import time
import configparser
import os
import json
from qr_reader import QRData
from camera import Camera
from reader_logic import ReaderLogic

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


cap = Camera()
qr = cv2.QRCodeDetector()
qr_reader = ReaderLogic(LOCATION, SCAN_COOLDOWN, checkin_checkout_duration)

scan_history = qr_reader.scan_history

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
                result = qr_reader.read_qr(token)
                if result and result["qr_data"]:
                    message_span = result["message"]
                    match (result["status"]):
                        case 0:
                            message_color = RED_COLOR
                            break
                        case 1:
                            message_color = GREEN_COLOR
                            break
                        case _:
                            message_color = WHITE_COLOR
                    drawText(frame, roi_x, roi_y - 10, message_span, message_color)
                    qr_data = QRData(
                        token, LOCATION, result["status"], int(time.time())
                    )
                    arranged_data = qr_data.write_data()
                    client.publish(MQTT_TOPIC, arranged_data)
                    print(result["message"])
                message_expiry_time = time.time() + send_interval
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
