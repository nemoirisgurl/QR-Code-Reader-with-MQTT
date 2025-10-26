import os
os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

import cv2
import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
import numpy as np  # <<< เพิ่ม
from qr_reader import QRData
from camera import Camera
from reader_logic import ReaderLogic, poll_mode_from_serial, apply_forced_mode
from datetime import datetime
from pyzbar.pyzbar import decode

CONFIG_FILE = "config.ini"
CV2_FRAME = "QR Code Scanner"
RED_COLOR   = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR  = (255, 0, 0)
YELLOW_COLOR= (255, 255, 0)
WHITE_COLOR = (255, 255, 255)
send_interval = 2
message_span = ""
message_expiry_time = 0

# อ่านไฟล์ config.ini
config = configparser.ConfigParser()
try:
    config.read(CONFIG_FILE)
    LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
    CHECKIN_CHECKOUT_DURATION = config.getint("Device", "StayDuration")
except Exception as e:
    print(f"Configure file error: {e}")
    raise SystemExit(1)

def drawText(frame, x, y, text, color=GREEN_COLOR):
    cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

def showResult(frame, roi_x, roi_y, reader_size, color):  # <<< แก้ให้รับพารามิเตอร์
    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + reader_size, roi_y + reader_size), color, 3)

def get_serial_port(baudrate=115200, timeout=1):
    try:
        while True:
            ports = list(serial.tools.list_ports.comports())
            if not ports:
                print("No serial ports found. Retrying in 2 seconds...")
                time.sleep(2); continue
            for p in ports:
                try:
                    ser = serial.Serial(p.device, baudrate, timeout=timeout)
                    print(f"Connected to serial port: {p.device}")
                    return ser
                except serial.SerialException:
                    continue
            print("No available serial ports. Retrying in 2 seconds...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("QR Code Reader is shutting down...")
        raise SystemExit

def get_camera():
    for cam in range(5):
        cap = Camera(camera_index=cam)
        if cap.cap.isOpened():
            print(f"Camera index {cam} is available.")
            return cap
        else:
            time.sleep(2)

ser = get_serial_port()
cap = get_camera()
qr_reader = ReaderLogic(LOCATION, SCAN_COOLDOWN, CHECKIN_CHECKOUT_DURATION)
timezone = pytz.timezone("Asia/Bangkok")
time_format = "%I:%M:%S %p"
token_format = re.compile(r"^[A-Za-z0-9_\-]{22}$")
scan_history = qr_reader.scan_history
check_mode = 1

cv2.namedWindow(CV2_FRAME, cv2.WINDOW_NORMAL)
# cv2.setWindowProperty(CV2_FRAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        try:
            check_mode = poll_mode_from_serial(ser, check_mode)
            ret, frame = cap.get_frame()
            if not ret or frame is None:
                cap.release()
                cap = get_camera()
                continue

            # กด q หรือหน้าต่างถูกปิด -> ออกจากลูป (ไม่ใช้ exit())
            if (cv2.waitKey(1) & 0xFF) == ord("q") or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1:
                print("QR Code Reading is shutting down.")
                break

            now_str = datetime.now(timezone).strftime(time_format)
            drawText(frame, 10, 30, now_str, YELLOW_COLOR)

            # ROI กลางจอ
            frame_h, frame_w, _ = frame.shape
            reader_size = int(min(frame_h, frame_w) * 0.5)
            roi_x = int((frame_w - reader_size) / 2)
            roi_y = int((frame_h - reader_size) / 2)
            roi_x2 = min(frame_w, roi_x + reader_size)   # <<< กันหลุดขอบ
            roi_y2 = min(frame_h, roi_y + reader_size)

            current_time = time.time()
            if current_time > message_expiry_time:
                message_span = ""

                roi_frame = frame[roi_y:roi_y2, roi_x:roi_x2]
                if roi_frame is None or roi_frame.size == 0:
                    cv2.imshow(CV2_FRAME, frame)
                    continue

                # <<< สำคัญ: ทำให้ภาพถูกใจ pyzbar
                roi_gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)                # 2D uint8
                roi_gray = np.ascontiguousarray(roi_gray, dtype=np.uint8)            # contiguous

                try:
                    decoded_objects = decode(roi_gray)
                except Exception as e:
                    print(f"decode error: {e} at: {datetime.now(timezone).strftime('%H:%M:%S')}")
                    decoded_objects = []

                for obj in decoded_objects:
                    token = obj.data.decode("utf-8")
                    if token_format.match(token):
                        result = qr_reader.read_qr(token)
                        result = apply_forced_mode(qr_reader, token, result, check_mode)
                        if result and result["qr_data"]:
                            message_span = result["message"]
                            status = result["status"]
                            message_color = GREEN_COLOR if status == 1 else RED_COLOR if status == 0 else WHITE_COLOR
                            if status != -1:
                                qr_data = QRData(token, LOCATION, status, int(time.time()))
                                try:
                                    ser.write(f"{token},{status},{now_str}\n".encode("utf-8"))
                                except serial.SerialException:
                                    print("Serial port disconnected. Attempting to reconnect...")
                                    try: ser.close()
                                    except Exception: pass
                                    ser = get_serial_port()
                                qr_data.write_data()
                            print(result["message"])
                            showResult(frame, roi_x, roi_y, reader_size, message_color)  # <<< เปลี่ยนการเรียก
                            drawText(frame, roi_x, roi_y - 50, f"{message_span} at: {now_str}", message_color)
                            break  # โค้ดแรกที่ valid ก็พอ

                message_expiry_time = time.time() + send_interval

            drawText(frame, roi_x, roi_y - 10, "Place QR Code here", BLUE_COLOR)
            cv2.rectangle(frame, (roi_x, roi_y), (roi_x + reader_size, roi_y + reader_size), (255, 255, 255), 3)

            cv2.imshow(CV2_FRAME, frame)

        except serial.SerialException:
            print("Serial port disconnected. Attempting to reconnect...")
            try: ser.close()
            except Exception: pass
            ser = get_serial_port()
        except Exception as e:
            print(f"Error: {e} at: {datetime.now(timezone).strftime('%H:%M:%S')}")
            continue

except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")

cap.release()
cv2.destroyAllWindows()
