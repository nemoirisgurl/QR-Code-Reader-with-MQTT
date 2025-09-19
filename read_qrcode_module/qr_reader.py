# ข้อมูลที่ได้จากการสแกน OR Code
import json
import os


class QR_Data:
    def __init__(self, token, location, status, timestamp=int):
        self.token = token
        self.location = location
        self.status = status
        self.timestamp = timestamp
        self.checkin_log = "checkin.json"
        self.checkout_log = "checkout.json"

    def get_data(self):
        return f"{self.token},{self.location},{self.status},{self.timestamp}"

    def compress_data(self):
        return {
            "token": self.token,
            "location": self.location,
            "status": self.status,
            "timestamp": self.timestamp,
        }

    def set_status(self, status):
        self.status = status

    def write_checkin_data(self):
        qr_obj = self.compress_data()
        all_logs = []
        try:
            if (
                os.path.exists(self.checkin_log)
                and os.path.getsize(self.checkin_log) > 0
            ):
                with open(self.checkin_log, "r", encoding="UTF-8") as log_file:
                    all_logs = json.load(log_file)
            all_logs.append(qr_obj)
            with open(self.checkin_log, "w", encoding="UTF-8") as log_file:
                json.dump(all_logs, log_file, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            with open(self.checkin_log, "w", encoding="UTF-8") as log_file:
                json.dump(list(qr_obj), log_file, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Log file error: {e}")
