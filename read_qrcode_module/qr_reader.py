# ข้อมูล
class QR_Data:
    def __init__(self, token, location, timestamp):
        self.token = token
        self.location = location
        self.timestamp = timestamp

    def get_data(self):
        return f"Token: {self.token}, Location: {self.location}, Timestamp: {self.timestamp}"
