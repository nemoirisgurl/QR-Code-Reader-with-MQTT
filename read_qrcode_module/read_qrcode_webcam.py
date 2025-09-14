import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time
import configparser
from qr_reader import QR_Data

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

CV2_FRAME = "QR Code Scanner"
RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (255, 0, 0)
YELLOW_COLOR = (255, 255, 0)
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


def drawText(frame, x, y, text, color=GREEN_COLOR):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
    thickness = 2
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


cap = cv2.VideoCapture(0)
qr = cv2.QRCodeDetector()

cv2.namedWindow(CV2_FRAME)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # กำหนดขนาดและตำแหน่งของพื้นที่สแกน QR Code
    frame_h, frame_w, _ = frame.shape
    roi_x = int((frame_w - READER_SIZE) / 2)
    roi_y = int((frame_h - READER_SIZE) / 2)

    cv2.rectangle(
        frame, (roi_x, roi_y), (roi_x + READER_SIZE, roi_y + READER_SIZE), BLUE_COLOR, 2
    )
    drawText(frame, roi_x, roi_y - 10, "Place QR Code Here", BLUE_COLOR)
    roi_frame = frame[roi_y : roi_y + READER_SIZE, roi_x : roi_x + READER_SIZE]
    current_time = time.time()
    if (current_time - last_scan_time) > SCAN_COOLDOWN:
        token, points, _ = qr.detectAndDecode(roi_frame)
        if points is not None and cv2.contourArea(points) > 0:
            if token:
                pts = np.int32(points + (roi_x, roi_y)).reshape((-1, 1, 2))
                if (
                    token != last_token
                    or (current_time - last_scan_time) > SCAN_COOLDOWN
                ):
                    time.sleep(0.5)
                    scan_time = int(current_time)
                    qr_data = QR_Data(token, LOCATION, scan_time)
                    arranged_data = qr_data.get_data()
                    print(arranged_data)
                    client.publish(MQTT_TOPIC, arranged_data)
                    cv2.polylines(
                        frame, [pts], isClosed=True, color=GREEN_COLOR, thickness=2
                    )
                    x, y = pts[0][0]
                    drawText(frame, x, y - 10, "Scanned", GREEN_COLOR)
                    last_token = token
                    last_scan_time = current_time
                else:
                    # รอ cooldown
                    cv2.polylines(
                        frame, [pts], isClosed=True, color=YELLOW_COLOR, thickness=2
                    )
                    x, y = pts[0][0]
                    drawText(frame, x, y - 10, "Wait...", YELLOW_COLOR)

        cv2.imshow(CV2_FRAME, frame)
        if (
            cv2.waitKey(1) == ord("q")
            or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1
        ):
            break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()
