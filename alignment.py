import cv2

def face_alignment_screen():
    cap = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    aligned = False

    while not aligned:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = cv2.flip(frame, 1)  # mirror
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

        # Draw central guide rectangle
        h, w, _ = frame.shape
        center_rect = (w//2 - 100, h//2 - 100, 200, 200)
        cv2.rectangle(frame, (center_rect[0], center_rect[1]),
                      (center_rect[0]+center_rect[2], center_rect[1]+center_rect[3]), (0,255,0), 2)

        # Check if any face is inside the center rectangle
        for (x, y, fw, fh) in faces:
            cv2.rectangle(frame, (x, y), (x+fw, y+fh), (255,0,0), 2)
            face_center = (x + fw//2, y + fh//2)
            if (center_rect[0] < face_center[0] < center_rect[0]+center_rect[2] and
                center_rect[1] < face_center[1] < center_rect[1]+center_rect[3]):
                aligned = True

        cv2.putText(frame, "Align your face inside the green box", (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
        cv2.imshow("Face Alignment", frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC to exit
            cap.release()
            cv2.destroyAllWindows()
            return False

    cap.release()
    cv2.destroyAllWindows()
    return True
