import cv2
import numpy as np

print(f"Python OpenCV version: {cv2.__version__}")
CV2_FRAME = 'QR Code Scanner'

def drawText(frame, x, y, text, color=(0, 255, 0)):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
    thickness = 2
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

cap = cv2.VideoCapture(0)
qr = cv2.QRCodeDetector()

cv2.namedWindow(CV2_FRAME)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detect and decode multiple QR codes
    retval, decoded_info, points, _ = qr.detectAndDecodeMulti(frame)

    if retval and points is not None:
        for qrcode, point in zip(decoded_info, points):
            pts = np.int32(point).reshape((-1, 1, 2))
            cv2.polylines(frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            x, y = pts[0][0]
            drawText(frame, x, y - 10, qrcode if qrcode else "Unknown")
            if qrcode:
                print(f"QR Code: {qrcode}")

    drawText(frame, 10, frame.shape[0] - 10, "Press q to exit", color=(0, 0, 255))

    cv2.imshow(CV2_FRAME, frame)
    if cv2.waitKey(1) == ord('q') or cv2.getWindowProperty(CV2_FRAME, cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()