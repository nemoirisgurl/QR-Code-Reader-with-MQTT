import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time

print(f"Python OpenCV version: {cv2.__version__}")
CV2_FRAME = 'QR Code Scanner'
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "openhouse/checkin-checkout"
SCAN_COOLDOWN = 5

last_token = None
last_scan_time = 0

client = mqtt.Client(protocol=mqtt.MQTTv311)
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()

def drawText(frame, x, y, text, color=(0, 255, 0)):
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

    # Detect and decode multiple QR codes
    retval, decoded_info, points, _ = qr.detectAndDecodeMulti(frame)

    if retval and points is not None:
        for token, point in zip(decoded_info, points):
            pts = np.int32(point).reshape((-1, 1, 2))
            current_time = time.time()
            x, y = pts[0][0]
            drawText(frame, x, y - 10, token if token else "Unknown", (0, 255, 0) if token else (0, 0, 255))
            if token != "":
                if (token != last_token or (current_time - last_scan_time) > SCAN_COOLDOWN):
                    cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                    scan_time = time.strftime("%H:%M:%S", time.localtime(current_time))
                    raw_data = f"Token: {token}, Time: {scan_time}"
                    print(raw_data)
                    client.publish(MQTT_TOPIC, raw_data)
                    last_token = token
                    last_scan_time = current_time
                else:
                    # รอ cooldown
                    cv2.polylines(frame, [pts], isClosed=True, color=(255, 255, 0), thickness=2)           
            else:
                # ไม่พบ token หรือ token ไม่ถูกต้อง
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 0, 255), thickness=2)
        

    cv2.imshow(CV2_FRAME, frame)
    if cv2.waitKey(1) == ord('q') or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()