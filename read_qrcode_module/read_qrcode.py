import cv2
import numpy as np
import paho.mqtt.client as mqtt
import time

print(f"Python OpenCV version: {cv2.__version__}")
CV2_FRAME = 'QR Code Scanner'
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "openhouse/checkin-checkout"
LOCATION = "Place1"
SCAN_COOLDOWN = 5
READER_SIZE= 300

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
    
    # กำหนดขนาดและตำแหน่งของพื้นที่สแกน QR Code
    frame_h, frame_w, _ = frame.shape
    roi_x = int((frame_w - READER_SIZE) / 2)
    roi_y = int((frame_h - READER_SIZE) / 2)

    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + READER_SIZE, roi_y + READER_SIZE), (255, 0, 0), 2)
    drawText(frame, roi_x, roi_y - 10, "Place QR Code Here", color=(255, 0, 0))
    roi_frame = frame[roi_y:roi_y + READER_SIZE, roi_x:roi_x + READER_SIZE]
    token, points, _ = qr.detectAndDecode(roi_frame)

    if points is not None:
        current_time = time.time()
        if token:
            pts = np.int32(points + (roi_x, roi_y)).reshape((-1, 1, 2))
            if (token != last_token or (current_time - last_scan_time) > SCAN_COOLDOWN):
                time.sleep(0.5)
                scan_time = time.strftime("%H:%M:%S", time.localtime(current_time))
                raw_data = f"{token},{scan_time}, {LOCATION}"
                print(f"Token: {token}, Time: {scan_time}, Location: {LOCATION}")
                client.publish(MQTT_TOPIC, raw_data)
                cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
                x, y = pts[0][0]
                drawText(frame, x, y - 10, "Scanned", color=(0, 255, 0))
                last_token = token
                last_scan_time = current_time
            else:
                # รอ cooldown
                cv2.polylines(frame, [pts], isClosed=True, color=(255, 255, 0), thickness=2) 
                x, y = pts[0][0]          
                drawText(frame, x, y - 10, "Wait...", color=(255, 255, 0))
            

    cv2.imshow(CV2_FRAME, frame)
    if cv2.waitKey(1) == ord('q') or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()