import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
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


ser = get_serial_port()
qr_reader = ReaderLogic(DEVICE_LOCATION, SCAN_COOLDOWN, checkin_checkout_duration)
scan_history = qr_reader.scan_history

try:
    while True:
        try:
            current_time = time.time()
            if current_time > message_expiry_time:
                message_span = ""
                token = input()
                if re.match(r"^[A-Za-z0-9_\-]{22}$", token):
                    result = qr_reader.read_qr(token)
                    if result["qr_data"] and result["status"] != -1:
                        qr_data = QRData(
                            token, DEVICE_LOCATION, result["status"], int(time.time())
                        )
                        ser.write(
                            (
                                f"{token},{result['status']},{result['message']}" + "\n"
                            ).encode("utf-8")
                        )
                        qr_data.write_data()
                        print(
                            f'{result["message"]} at: {datetime.now(pytz.timezone("Asia/bangkok")).strftime("%H:%M:%S")}'
                        )
                    message_expiry_time = time.time() + send_interval
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
