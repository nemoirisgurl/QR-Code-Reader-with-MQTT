import cv2


class Camera:
    def __init__(self):
        self.camera_index = 0
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            print("Camera failed")
        print("Camera opened")

    def get_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            print("No QR Code")
        return ret, frame

    def release(self):
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
