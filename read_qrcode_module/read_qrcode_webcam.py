import os
# ถ้าใช้ Wayland/xrdp ให้เปิดบรรทัดนี้ก่อน import cv2
os.environ.setdefault("QT_QPA_PLATFORM","xcb")

import cv2
import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
import numpy as np
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
message_expiry_time = 0

# --- config ---
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
    cv2.putText(frame, text, (x, y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2, cv2.LINE_AA)

def showResult(frame, roi_x, roi_y, reader_size, color):
    cv2.rectangle(frame, (roi_x, roi_y),
                  (roi_x + reader_size, roi_y + reader_size), color, 3)

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

def get_camera(max_index=5, retry_delay=2):
    while True:
        for cam in range(max_index):
            cap = Camera(camera_index=cam)
            if cap.cap.isOpened():
                print(f"Camera index {cam} is available.")
                return cap
        print("No available camera devices. Retrying in 2 seconds...")
        time.sleep(retry_delay)

ser = get_serial_port()
cap = get_camera()

qr_reader = ReaderLogic(LOCATION, SCAN_COOLDOWN, CHECKIN_CHECKOUT_DURATION)
timezone = pytz.timezone("Asia/Bangkok")
time_format = "%I:%M:%S %p"
token_format = re.compile(r"^[A-Za-z0-9_\-]{22}$")
check_mode = 1

cv2.namedWindow(CV2_FRAME, cv2.WINDOW_NORMAL)
# ถ้า remote ผ่าน xrdp/Wayland แนะนำคอมเมนต์บรรทัด fullscreen นี้
# cv2.setWindowProperty(CV2_FRAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

bad_frames = 0

def process_token(token, now_str):
    if not token_format.match(token):
        return None
    result = qr_reader.read_qr(token)
    result = apply_forced_mode(qr_reader, token, result, check_mode)
    if result and result.get("qr_data"):
        status = result["status"]
        if status != -1:
            qr_data = QRData(token, LOCATION, status, int(time.time()))
            try:
                ser.write(f"{token},{status},{now_str}\n".encode("utf-8"))
            except serial.SerialException:
                print("Serial port disconnected. Attempting to reconnect...")
                try: ser.close()
                except Exception: pass
                new_ser = get_serial_port()
                globals()["ser"] = new_ser
            qr_data.write_data()
        print(result["message"])
        return result
    return None

try:
    while True:
        try:
            check_mode = poll_mode_from_serial(ser, check_mode)

            ret, frame = cap.get_frame()
            if not ret or frame is None:
                bad_frames += 1
                if bad_frames >= 5:
                    cap.release()
                    cap = get_camera()
                    bad_frames = 0
                continue
            bad_frames = 0

            frame_h, frame_w, _ = frame.shape
            reader_size = max(80, int(min(frame_h, frame_w) * 0.5))
            roi_x = max(0, int((frame_w - reader_size) / 2))
            roi_y = max(0, int((frame_h - reader_size) / 2))
            roi_x2 = min(frame_w, roi_x + reader_size)
            roi_y2 = min(frame_h, roi_y + reader_size)

            now_str = datetime.now(timezone).strftime(time_format)
            drawText(frame, 10, 30, now_str, YELLOW_COLOR)

            current_time = time.time()
            if current_time > message_expiry_time:
                # เตรียม ROI ให้ปลอดภัยสำหรับ pyzbar
                roi_frame = frame[roi_y:roi_y2, roi_x:roi_x2]
                if roi_frame is None or roi_frame.size == 0:
                    cv2.imshow(CV2_FRAME, frame)
                    if (cv2.waitKey(1) & 0xFF) == ord("q"): break
                    continue

                roi_gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
                roi_gray = np.ascontiguousarray(roi_gray, dtype=np.uint8)

                try:
                    decoded_objects = decode(roi_gray)
                except Exception as e:
                    print(f"decode error: {e} at: {datetime.now(timezone).strftime('%H:%M:%S')}")
                    decoded_objects = []

                for obj in decoded_objects:
                    token = obj.data.decode("utf-8")
                    result = process_token(token, now_str)
                    if result:
                        color = GREEN_COLOR if result["status"] == 1 else (RED_COLOR if result["status"] == 0 else WHITE_COLOR)
                        showResult(frame, roi_x, roi_y, reader_size, color)
                        drawText(frame, roi_x, roi_y - 50, f"{result['message']} at: {now_str}", color)
                        break  # แค่โค้ดแรกที่ valid

                message_expiry_time = time.time() + send_interval

            drawText(frame, roi_x, roi_y - 10, "Place QR Code here", BLUE_COLOR)
            cv2.rectangle(frame, (roi_x, roi_y), (roi_x + reader_size, roi_y + reader_size), (255, 255, 255), 3)

            cv2.imshow(CV2_FRAME, frame)
            if (cv2.waitKey(1) & 0xFF) == ord("q") \
               or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1:
                print("QR Code Reading is shutting down.")
                break  # ← ไม่ใช้ exit()

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
