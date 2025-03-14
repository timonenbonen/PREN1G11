import cv2
import numpy as np
import HandTrackingModule as htm
import time
import pyautogui


def main():
    # Parameter für die Kamera und Maussteuerung
    wCam, hCam = 640, 480
    frameR = 100  # Frame Reduction (Rahmen)
    smoothening = 7  # Glättungsfaktor

    # Variablen für die Mausposition und Zeiterfassung
    pTime = 0
    plocX, plocY = 0, 0
    clocX, clocY = 0, 0

    # Kamera einrichten - mit verbesserter Fehlerbehandlung
    # Versuche verschiedene Kameraoptionen
    camera_options = [
        0,  # Standard-Webcam
        1,  # Zweite Kamera (falls vorhanden)
        "http://192.168.178.21:4747/video"  # DroidCam
    ]

    cap = None
    for camera in camera_options:
        print(f"Versuche Verbindung mit Kamera: {camera}")
        cap = cv2.VideoCapture(camera)
        cap.set(3, wCam)
        cap.set(4, hCam)

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

    # Hand-Tracking-Modul initialisieren
    detector = htm.handDetector(maxHands=1)

    # Bildschirmgröße ermitteln
    wScr, hScr = pyautogui.size()

    # Mausbewegung sicherer machen
    pyautogui.FAILSAFE = True

    while True:
        # 1. Hand-Landmarken finden
        success, img = cap.read()
        if not success or img is None or img.size == 0:
            print("Fehler beim Lesen des Kamera-Feeds")
            time.sleep(0.5)
            continue

        # Prüfen auf einfarbigen (blauen) Bildschirm
        if len(np.unique(img.reshape(-1, img.shape[2]), axis=0)) < 5:
            print("Warnung: Möglicherweise einfarbiger Frame (blauer Bildschirm?)")
            time.sleep(0.5)
            continue

        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)

        # 2. Position der Fingerspitzen ermitteln
        if len(lmList) != 0:
            x1, y1 = lmList[8][1:]  # Index-Fingerspitze
            x2, y2 = lmList[12][1:]  # Mittelfingerspitze

            # 3. Prüfen, welche Finger gehoben sind
            fingers = detector.fingersUp()

            # Begrenzungsrahmen zeichnen
            cv2.rectangle(img, (frameR, frameR), (wCam - frameR, hCam - frameR),
                          (255, 0, 255), 2)

            # 4. Bewegungsmodus: Nur Zeigefinger oben
            if fingers[1] == 1 and fingers[2] == 0:
                # 5. Koordinaten umrechnen
                x3 = np.interp(x1, (frameR, wCam - frameR), (0, wScr))
                y3 = np.interp(y1, (frameR, hCam - frameR), (0, hScr))

                # 6. Werte glätten
                clocX = plocX + (x3 - plocX) / smoothening
                clocY = plocY + (y3 - plocY) / smoothening

                # 7. Mausbewegung - Angepasst für PyAutoGUI
                try:
                    # PyAutoGUI verwendet die direkte Position, während autopy die X-Koordinate invertiert
                    pyautogui.moveTo(clocX, clocY)
                except pyautogui.FailSafeException:
                    print("Maus hat den Rand des Bildschirms erreicht (FailSafe)")

                cv2.circle(img, (x1, y1), 15, (255, 0, 255), cv2.FILLED)
                plocX, plocY = clocX, clocY

            # 8. Klickmodus: Zeige- und Mittelfinger oben
            if fingers[1] == 1 and fingers[2] == 1:
                # 9. Abstand zwischen den Fingern messen
                length, img, lineInfo = detector.findDistance(8, 12, img)

                # 10. Mausklick bei kurzem Abstand
                if length < 40:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                    pyautogui.click()  # Linksklick
                    # Kurze Verzögerung, um Mehrfachklicks zu vermeiden
                    time.sleep(0.3)

        # 11. Framerate berechnen
        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime
        cv2.putText(img, str(int(fps)), (20, 50), cv2.FONT_HERSHEY_PLAIN, 3,
                    (255, 0, 0), 3)

        # 12. Anzeige
        cv2.imshow("Mouse Controller", img)

        # Beenden mit ESC-Taste
        if cv2.waitKey(1) & 0xFF == 27:
            break

    # Ressourcen freigeben
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()