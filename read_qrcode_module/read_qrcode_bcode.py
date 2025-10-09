import sys
import time
import configparser
import pytz
import re
import serial
import serial.tools.list_ports
from qr_reader import QRData
from reader_logic import ReaderLogic, poll_mode_from_serial, apply_forced_mode
from datetime import datetime
from threading import Thread
from queue import Queue, Empty

CONFIG_FILE = "config.ini"
send_interval = 2
message_span = ""
message_expiry_time = 0

# อ่านไฟล์ config.ini
config = configparser.ConfigParser()

try:
    config.read(CONFIG_FILE)
    DEVICE_LOCATION = config.get("Device", "Location")
    SCAN_COOLDOWN = config.getint("Device", "ScanCooldown")
    CHECKIN_CHECKOUT_DURATION = config.getint("Device", "StayDuration")
except Exception as e:
    print(f"Configure file error: {e}")
    exit()

def stdin_reader(q: Queue): 
    try: 
        for line in sys.stdin: 
            q.put(line.strip()) 
    except Exception: 
        pass

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
        print("QR Code Reading is shutting down.")
        exit()


ser = get_serial_port()
qr_reader = ReaderLogic(DEVICE_LOCATION, SCAN_COOLDOWN, CHECKIN_CHECKOUT_DURATION)
timezone = pytz.timezone("Asia/Bangkok")
time_format = "%I:%M:%S %p"
token_format = re.compile(r"^[A-Za-z0-9_\-]{22}$")
scan_history = qr_reader.scan_history
check_mode = 1

q = Queue()
t = Thread(target=stdin_reader, args=(q,), daemon=True)
t.start()

try:
    while True:
        try:
            current_time = time.time()
            check_mode = poll_mode_from_serial(ser, check_mode)
            if current_time > message_expiry_time:
                message_span = ""
                try:
                    token = q.get_nowait()
                except Empty:
                    time.sleep(0.01)
                    continue
                if token_format.match(token):
                    result = qr_reader.read_qr(token)
                    result = apply_forced_mode(qr_reader, token, result, check_mode)
                    if result["qr_data"] and result["status"] != -1:
                        qr_data = QRData(
                            token, DEVICE_LOCATION, result["status"], int(time.time())
                        )
                        try:
                            ser.write(
                                (
                                    f"{token},{result['status']},{datetime.now(timezone).strftime(time_format)}" + "\n"
                                ).encode("utf-8")
                            )
                            qr_data.write_data()
                            print(
                                f'{result["message"]} at: {datetime.now(timezone).strftime(time_format)}'
                            )
                        except serial.SerialException:
                            print("Serial port disconnected. Attempting to reconnect...")
                            ser.close()
                            ser = get_serial_port()
                    message_expiry_time = time.time() + send_interval
                    print(scan_history)

        except serial.SerialException:
            print("Serial port disconnected. Attempting to reconnect...")
            ser = get_serial_port()
        except Exception as e:
            print(
                f'Error: {e} at: {datetime.now(timezone).strftime(time_format)}'
            )
            continue



except KeyboardInterrupt:
    print("QR Code Reader is shutting down...")
