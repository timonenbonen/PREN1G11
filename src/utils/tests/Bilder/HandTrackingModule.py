import cv2
import mediapipe as mp
import time
import math
import numpy as np


class handDetector():
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.maxHands,
            min_detection_confidence=self.detectionCon,
            min_tracking_confidence=self.trackCon
        )
        self.mpDraw = mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []

    def findHands(self, img, draw=True):
        # Sicherheitscheck für gültige Frames
        if img is None or img.size == 0:
            print("Warnung: Leerer Frame in findHands")
            return img

        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)

        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList = []
        yList = []
        bbox = []
        self.lmList = []

        # Sicherheitscheck für gültige Frames
        if img is None or img.size == 0:
            print("Warnung: Leerer Frame in findPosition")
            return self.lmList, bbox

        if hasattr(self, 'results') and self.results.multi_hand_landmarks:
            if handNo < len(self.results.multi_hand_landmarks):
                myHand = self.results.multi_hand_landmarks[handNo]
                for id, lm in enumerate(myHand.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    xList.append(cx)
                    yList.append(cy)
                    self.lmList.append([id, cx, cy])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

                if xList and yList:
                    xmin, xmax = min(xList), max(xList)
                    ymin, ymax = min(yList), max(yList)
                    bbox = xmin, ymin, xmax, ymax

                    if draw:
                        cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20),
                                      (0, 255, 0), 2)

        return self.lmList, bbox

    def fingersUp(self):
        fingers = []
        # Überprüfen, ob lmList existiert und genügend Punkte enthält
        if not hasattr(self, 'lmList') or len(self.lmList) == 0:
            return [0, 0, 0, 0, 0]  # Standardmäßig keine Finger hoch

        if len(self.lmList) > self.tipIds[0]:
            # Thumb
            if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
                fingers.append(1)
            else:
                fingers.append(0)

            # Fingers
            for id in range(1, 5):
                if len(self.lmList) > self.tipIds[id]:
                    if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)
                else:
                    fingers.append(0)  # Wenn der Fingerpunkt nicht gefunden wurde

        # Auffüllen, falls nicht alle Finger erkannt wurden
        while len(fingers) < 5:
            fingers.append(0)

        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        # Überprüfen, ob das Bild gültig ist
        if img is None or img.size == 0:
            return 0, img, [0, 0, 0, 0, 0, 0]

        # Überprüfen, ob die Punkte in lmList vorhanden sind
        if not hasattr(self, 'lmList') or len(self.lmList) <= max(p1, p2):
            return 0, img, [0, 0, 0, 0, 0, 0]

        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)

        length = math.hypot(x2 - x1, y2 - y1)
        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    pTime = 0
    cTime = 0

    # Kameraoptionen durchprobieren
    camera_options = [
        0,  # Standard-Webcam
        1,  # Zweite Kamera (falls vorhanden)
        "http://192.168.178.21:4747/video"  # DroidCam
    ]

    cap = None
    for camera in camera_options:
        print(f"Versuche Verbindung mit Kamera: {camera}")
        cap = cv2.VideoCapture(camera)

        # Teste, ob die Kamera funktioniert
        test_counter = 0
        while test_counter < 3:
            ret, test_frame = cap.read()
            if ret and test_frame is not None and test_frame.size > 0:
                # Prüfe, ob der Frame nicht nur aus einer Farbe besteht
                if len(np.unique(test_frame.reshape(-1, test_frame.shape[2]), axis=0)) > 5:
                    print(f"Kameraverbindung erfolgreich mit Option: {camera}")
                    break
            print(f"Versuch {test_counter + 1}: Kein gültiger Frame")
            test_counter += 1
            time.sleep(0.5)

        if test_counter < 3:
            break  # Erfolgreiche Kameraverbindung hergestellt
        else:
            cap.release()  # Diese Kamera freigeben und die nächste versuchen
            cap = None

    if cap is None:
        print("Konnte keine Verbindung zu einer Kamera herstellen.")
        print("Bitte überprüfen Sie:")
        print("1. Ist die Kamera angeschlossen und funktioniert?")
        print("2. Wird die Kamera von einer anderen Anwendung verwendet?")
        print("3. Falls Sie DroidCam verwenden: Läuft die App und stimmt die IP-Adresse?")
        return

    detector = handDetector()

    while True:
        success, img = cap.read()
        if not success or img is None or img.size == 0:
            print("Fehler beim Lesen des Kamera-Feeds. Versuche erneut zu verbinden...")
            # Kurze Pause und erneuter Verbindungsversuch
            time.sleep(1)
            continue

        # Prüfen auf einfarbigen (blauen) Bildschirm
        if len(np.unique(img.reshape(-1, img.shape[2]), axis=0)) < 5:
            print("Warnung: Möglicherweise einfarbiger Frame (blauer Bildschirm?)")
            time.sleep(0.5)
            continue

        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)
        if len(lmList) != 0:
            print(lmList[4])  # Zeigt Position des Daumens

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 255), 3)

        cv2.imshow("Hand Tracking", img)

        # Ende mit Escape-Taste
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Ressourcen freigeben
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()