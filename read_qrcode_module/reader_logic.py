import time
import json
import os


class ReaderLogic:
    def __init__(self, location, cooldown, checkin_checkout_duration):
        self.location = location
        self.cooldown = cooldown
        self.checkin_checkout_duration = checkin_checkout_duration
        self.qr_log = "qr_log.json"
        self.scan_history = self.load_data()

    def load_data(self):
        if not os.path.exists("qr_log.json") or os.path.getsize("qr_log.json") == 0:
            print("QR Log created")
            return {}
        try:
            with open("qr_log.json", "r", encoding="UTF-8") as log_file:
                history = {}
                all_logs = json.load(log_file)
                all_logs = all_logs[-800:]
                for log in reversed(all_logs):
                    token = log.get("token")
                    timestamp = log.get("epoch")
                    if token and timestamp and token not in history:
                        if log.get("check") == 1:
                            history[token] = timestamp
        except Exception as e:
            print(f"Log file error: {e}")
            return {}
        return history

    def read_qr(self, token):
        timestamp = int(time.time())
        if token in self.scan_history:
            last_scan_time = self.scan_history[token]
            time_diff = timestamp - last_scan_time
            if time_diff < self.cooldown:
                status = -1
                message = "Wait..."
            elif time_diff > self.checkin_checkout_duration:
                status = 0
                del self.scan_history[token]
                message = "Checked out"
            else:
                status = 1
                self.scan_history[token] = timestamp
                message = "Rechecked in"
        else:
            status = 1
            self.scan_history[token] = timestamp
            message = "Checked in"
        qr_data = f"{token},{self.location},{status},{timestamp}"
        return {"status": status, "message": message, "qr_data": qr_data}
