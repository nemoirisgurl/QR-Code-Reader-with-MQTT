import cv2
import time
import threading


class Camera:
    def __init__(self, camera_index=0, width=640, height=480):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("Camera failed")
        print("Camera opened")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.ret = False
        self.frame = None
        self.is_running = True

        self.thread = threading.Thread(target=self.update_frame, daemon=True)
        self.thread.start()
        actual_width = self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_height = self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        print(
            f"📷 Camera at index {self.camera_index} opened with resolution: {int(actual_width)}x{int(actual_height)}"
        )

    def update_frame(self):
        while self.is_running:
            ret, frame = self.cap.read()
            if ret:
                self.ret = True
                self.frame = frame
            else:
                time.sleep(0.01)

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("No QR Code")
        return ret, frame.copy()

    def release(self):
        self.is_running = False
        self.thread.join()
        if self.cap.isOpened():
            self.cap.release()


if __name__ == "__main__":
    cam = Camera()
    cv2.namedWindow("Camera Test | Press 'q' to exit")
    while True:
        ret, frame = cam.get_frame()
        if not ret:
            print("Shut down")
            break
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        cv2.imshow("Camera Test | Press 'q' to exit", frame)
    cam.release()
    cv2.destroyAllWindows()
