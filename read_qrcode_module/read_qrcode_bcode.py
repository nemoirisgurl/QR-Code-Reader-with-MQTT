import time
import configparser
import pytz
import serial
from qr_reader import QRData
from reader_logic import ReaderLogic
from datetime import datetime


CONFIG_FILE = "config.ini"
checkin_checkout_duration = 300
send_interval = 2
message_span = ""
message_expiry_time = 0

# อ่านไฟล์ config.ini
config = configparser.ConfigParser()

try:
    config.read(CONFIG_FILE)
    DEVICE_LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=1)
qr_reader = ReaderLogic(DEVICE_LOCATION, SCAN_COOLDOWN, checkin_checkout_duration)
scan_history = qr_reader.scan_history

try:
    while True:
        current_time = time.time()
        if current_time > message_expiry_time:
            message_span = ""
            token = input()
            if len(token) == 22:
                result = qr_reader.read_qr(token)
                if result["qr_data"] and result["status"] != -1:
                    qr_data = QRData(
                        token, DEVICE_LOCATION, result["status"], int(time.time())
                    )
                    arranged_data = qr_data.get_data()
                    ser.write((arranged_data + "\n").encode("utf-8"))
                    qr_data.write_data()
                    print(
                        f'{result["message"]} at: {datetime.now(pytz.timezone("Asia/bangkok")).strftime("%H:%M:%S")}'
                    )
                message_expiry_time = time.time() + send_interval


except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")
