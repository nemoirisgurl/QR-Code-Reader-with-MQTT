# ข้อมูลที่ได้จากการสแกน OR Code
import json
import os


class QR_Data:
    def __init__(self, token, location, status, timestamp=int):
        self.token = token
        self.location = location
        self.status = status
        self.timestamp = timestamp
        self.log_json = "qr_log.json"

    def get_data(self):
        return f"{self.token},{self.location},{self.status},{self.timestamp}"

    def write_data(self):
        qr_obj = {
            "token": self.token,
            "location": self.location,
            "status": self.status,
            "timestamp": self.timestamp,
        }
        all_logs = []
        try:
            if os.path.exists(self.log_json) and os.path.getsize(self.log_json) > 0:
                with open(self.log_json, "r", encoding="UTF-8") as log_file:
                    all_logs = json.load(log_file)
            all_logs.append(qr_obj)
            with open(self.log_json, "w", encoding="UTF-8") as log_file:
                json.dump(all_logs, log_file, indent=4, ensure_ascii=False)
        except json.JSONDecodeError:
            with open(self.log_json, "w", encoding="UTF-8") as log_file:
                json.dump(list(qr_obj), log_file, indent=4, ensure_ascii=False)

        except Exception as e:
            print(f"Log file error: {e}")
