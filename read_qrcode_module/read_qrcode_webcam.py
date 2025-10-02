import cv2
import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
from qr_reader import QRData
from camera import Camera
from reader_logic import ReaderLogic
from datetime import datetime
from pyzbar.pyzbar import decode

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
    LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()


def drawText(frame, x, y, text, color=GREEN_COLOR):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    thickness = 2
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


def showResult(color):
    cv2.rectangle(
        frame,
        (roi_x, roi_y),
        (roi_x + reader_size, roi_y + reader_size),
        color,
        3,
    )


def get_serial_port(baudrate=115200, timeout=1):
    while True:
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("No serial ports found. Retrying in 2 seconds...")
            time.sleep(2)
            continue
        for p in ports:
            try:
                ser = serial.Serial(p.device, baudrate, timeout=timeout)
                print(f"Connected to serial port: {p.device}")
                return ser
            except serial.SerialException:
                continue
        print("No available serial ports. Retrying in 2 seconds...")
        time.sleep(2)


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
qr = cv2.QRCodeDetector()
qr_reader = ReaderLogic(LOCATION, SCAN_COOLDOWN, checkin_checkout_duration)

scan_history = qr_reader.scan_history

cv2.namedWindow(CV2_FRAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(CV2_FRAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        try:
            ret, frame = cap.get_frame()
            if not ret or frame is None:
                cap.release()
                cap = get_camera()
                continue
            if (
                cv2.waitKey(1) & 0xFF == ord("q")
                or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1
            ):
                print("QR Code Reading is shutting down.")
                exit()
            drawText(
                frame,
                10,
                30,
                datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S"),
                YELLOW_COLOR,
            )
            # กำหนดขนาดและตำแหน่งของพื้นที่สแกน QR Code

            frame_h, frame_w, _ = frame.shape
            reader_size = int(min(frame_h, frame_w) * 0.4)
            roi_x = int((frame_w - reader_size) / 2)
            roi_y = int((frame_h - reader_size) / 2)

            current_time = time.time()
            if current_time > message_expiry_time:
                message_span = ""
                roi_frame = frame[
                    roi_y : roi_y + reader_size, roi_x : roi_x + reader_size
                ]
                decoded_objects = decode(roi_frame)

                for obj in decoded_objects:
                    token = obj.data.decode("utf-8")
                    if re.match(r"^[A-Za-z0-9_\-]{22}", token):
                        result = qr_reader.read_qr(token)
                        if result and result["qr_data"]:
                            message_span = result["message"]
                            match (result["status"]):
                                case 0:
                                    message_color = RED_COLOR
                                case 1:
                                    message_color = GREEN_COLOR
                                case _:
                                    message_color = WHITE_COLOR
                            if result["status"] != -1:
                                qr_data = QRData(
                                    token, LOCATION, result["status"], int(time.time())
                                )
                                ser.write(
                                    (
                                        f"{token},{result['status']},{result['message']}"
                                        + "\n"
                                    ).encode("utf-8")
                                )
                                qr_data.write_data()
                            print(result["message"])
                            showResult(message_color)
                            drawText(
                                frame,
                                roi_x,
                                roi_y - 50,
                                f"{message_span} at: {datetime.now(pytz.timezone("Asia/Bangkok")).strftime("%H:%M:%S")}",
                                message_color,
                            )
                        message_expiry_time = time.time() + send_interval
                drawText(frame, roi_x, roi_y - 10, "Place QR Code here", BLUE_COLOR)
                cv2.rectangle(
                    frame,
                    (roi_x, roi_y),
                    (roi_x + reader_size, roi_y + reader_size),
                    (255, 255, 255),
                    3,
                )
                cv2.imshow(CV2_FRAME, frame)
        except serial.SerialException:
            print("Serial port disconnected. Attempting to reconnect...")
            ser.close()
            ser = get_serial_port()
        except Exception as e:
            print(
                f"Error: {e} at: {datetime.now(pytz.timezone("Asia/bangkok")).strftime("%H:%M:%S")}"
            )
            continue

except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")
cap.release()
cv2.destroyAllWindows()
