import cv2
import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
from qr_reader import QRData
from camera import Camera
from reader_logic import ReaderLogic, poll_mode_from_serial, apply_forced_mode
from datetime import datetime
from pyzbar.pyzbar import decode
from evdev import InputDevice, ecodes, categorize
from queue import Queue, Empty

CONFIG_FILE = "config.ini"
CV2_FRAME = "QR Code Scanner"
RED_COLOR = (0, 0, 255)
GREEN_COLOR = (0, 255, 0)
BLUE_COLOR = (255, 0, 0)
YELLOW_COLOR = (255, 255, 0)
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
    exit()

# --- evdev-based input for USB barcode scanner on Pi + xrdp ---

SHIFT_KEYS = {ecodes.KEY_LEFTSHIFT, ecodes.KEY_RIGHTSHIFT}

# แผนที่คีย์สำหรับ base64url-ish token: [A-Za-z0-9_-]
KEYMAP = {
    # digits row
    ecodes.KEY_0:'0', ecodes.KEY_1:'1', ecodes.KEY_2:'2', ecodes.KEY_3:'3', ecodes.KEY_4:'4',
    ecodes.KEY_5:'5', ecodes.KEY_6:'6', ecodes.KEY_7:'7', ecodes.KEY_8:'8', ecodes.KEY_9:'9',
    # letters
    ecodes.KEY_A:'a', ecodes.KEY_B:'b', ecodes.KEY_C:'c', ecodes.KEY_D:'d', ecodes.KEY_E:'e',
    ecodes.KEY_F:'f', ecodes.KEY_G:'g', ecodes.KEY_H:'h', ecodes.KEY_I:'i', ecodes.KEY_J:'j',
    ecodes.KEY_K:'k', ecodes.KEY_L:'l', ecodes.KEY_M:'m', ecodes.KEY_N:'n', ecodes.KEY_O:'o',
    ecodes.KEY_P:'p', ecodes.KEY_Q:'q', ecodes.KEY_R:'r', ecodes.KEY_S:'s', ecodes.KEY_T:'t',
    ecodes.KEY_U:'u', ecodes.KEY_V:'v', ecodes.KEY_W:'w', ecodes.KEY_X:'x', ecodes.KEY_Y:'y',
    ecodes.KEY_Z:'z',
    # symbols we accept
    ecodes.KEY_MINUS:'-',  # '_' จะมาจาก Shift + MINUS
    # keypad (รองรับ NumLock ทั้งคู่)
    ecodes.KEY_KP0:'0', ecodes.KEY_KP1:'1', ecodes.KEY_KP2:'2', ecodes.KEY_KP3:'3', ecodes.KEY_KP4:'4',
    ecodes.KEY_KP5:'5', ecodes.KEY_KP6:'6', ecodes.KEY_KP7:'7', ecodes.KEY_KP8:'8', ecodes.KEY_KP9:'9',
}

def evdev_reader(dev_path, q):
    dev = InputDevice(dev_path)
    buf = []
    shift = False
    for event in dev.read_loop():
        if event.type != ecodes.EV_KEY:
            continue
        ke = categorize(event)

        # track shift
        if ke.scancode in SHIFT_KEYS:
            shift = (ke.keystate == 1)  # 1=down, 0=up
            continue

        if ke.keystate != 1:  # key down only
            continue

        # ENTER or KEYPAD ENTER → ส่งหนึ่งบรรทัด
        if ke.keycode in ('KEY_ENTER', 'KEY_KPENTER'):
            token = ''.join(buf).strip()
            buf.clear()
            if token:
                q.put(token)
            continue

        ch = KEYMAP.get(ke.scancode)
        if not ch:
            continue

        # uppercase when shift
        if 'a' <= ch <= 'z' and shift:
            ch = ch.upper()
        # underscore when Shift + minus
        if ch == '-' and shift:
            ch = '_'

        buf.append(ch)

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
    try:
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
    except KeyboardInterrupt:
        print("QR Code Reader is shutting down...")
        exit()


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
qr_reader = ReaderLogic(LOCATION, SCAN_COOLDOWN, CHECKIN_CHECKOUT_DURATION)
timezone = pytz.timezone("Asia/Bangkok")
time_format = "%I:%M:%S %p"
token_format = re.compile(r"^[A-Za-z0-9_\-]{22}$")
scan_history = qr_reader.scan_history
check_mode = 1

cv2.namedWindow(CV2_FRAME, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(CV2_FRAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        try:
            check_mode = poll_mode_from_serial(ser, check_mode)
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
                datetime.now(timezone).strftime(time_format),
                YELLOW_COLOR,
            )
            # กำหนดขนาดและตำแหน่งของพื้นที่สแกน QR Code

            frame_h, frame_w, _ = frame.shape
            reader_size = int(min(frame_h, frame_w) * 0.5)
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
                    if token_format.match(token):
                        result = qr_reader.read_qr(token)
                        result = apply_forced_mode(qr_reader, token, result, check_mode)
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
                                try:
                                    ser.write(
                                        (
                                            f"{token},{result['status']},{datetime.now(timezone).strftime(time_format)}"
                                            + "\n"
                                        ).encode("utf-8")
                                    )
                                except serial.SerialException:
                                    print("Serial port disconnected. Attempting to reconnect...")
                                    ser.close()
                                    ser = get_serial_port()
                                qr_data.write_data()
                            print(result["message"])
                            showResult(message_color)
                            drawText(
                                frame,
                                roi_x,
                                roi_y - 50,
                                f"{message_span} at: {datetime.now(timezone).strftime(time_format)}",
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
                f"Error: {e} at: {datetime.now(timezone).strftime('%H:%M:%S')}"
            )
            continue

except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")
cap.release()
cv2.destroyAllWindows()
