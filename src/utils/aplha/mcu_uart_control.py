import serial
import time

class MCUCommunicator:
    """
    Eine Klasse zur Steuerung eines MCUs über eine UART-Schnittstelle
    basierend auf einem definierten Kommunikationsprotokoll.
    """

    def __init__(self, port='/dev/serial0', baudrate=9600, timeout=2.0):
        """
        Initialisiert den MCUCommunicator.

        Args:
            port (str): Der serielle Port (z.B. '/dev/serial0' oder 'COM3').
            baudrate (int): Die Baudrate für die serielle Kommunikation.
            timeout (float): Die maximale Wartezeit für eine Antwort vom MCU in Sekunden.
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self._connect()

    def _connect(self):
        """Stellt die serielle Verbindung her."""
        if self.ser and self.ser.is_open:
            print("Verbindung ist bereits offen.")
            return True
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=self.timeout)
            print(f"Serielle Verbindung auf {self.port} mit {self.baudrate} Baud geöffnet.")
            # Kurze Pause, um dem MCU Zeit zum Initialisieren zu geben, falls nötig
            time.sleep(0.5) # Reduziert, da oft nicht so lange nötig
            return True
        except serial.SerialException as e:
            print(f"Fehler beim Öffnen der seriellen Verbindung auf {self.port}: {e}")
            self.ser = None
            return False

    def disconnect(self):
        """Schließt die serielle Verbindung."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serielle Verbindung geschlossen.")
        self.ser = None

    @property
    def is_connected(self):
        """Prüft, ob die serielle Verbindung aktiv ist."""
        return self.ser is not None and self.ser.is_open

    def _send_and_receive_raw_command(self, command_string):
        """
        Sendet einen rohen Befehlsstring an den MCU und wartet auf eine Antwort.

        Args:
            command_string (str): Der zu sendende Befehl, endend mit ';'.

        Returns:
            str: Die Antwort vom MCU oder None bei Fehler/Timeout.
        """
        if not self.is_connected:
            print("Fehler: Serielle Verbindung nicht geöffnet. Versuche erneut zu verbinden...")
            if not self._connect():
                print("Verbindung konnte nicht hergestellt werden.")
                return None

        try:
            print(f"Sende: {command_string}")
            self.ser.write(command_string.encode('utf-8')) # Befehl als Bytes senden
            self.ser.flush() # Sicherstellen, dass alle Daten gesendet werden

            # Auf Antwort warten (endet mit ';')
            response_bytes = self.ser.read_until(b';')
            response_str = response_bytes.decode('utf-8').strip()

            if response_str:
                print(f"Empfangen: {response_str}")
            else:
                print("Keine Antwort vom MCU innerhalb des Timeouts erhalten.")
            return response_str

        except serial.SerialException as e:
            print(f"Serial Exception während der Kommunikation: {e}")
            self.disconnect() # Verbindung bei Fehler ggf. zurücksetzen
            return None
        except Exception as e:
            print(f"Allgemeiner Fehler während der Kommunikation: {e}")
            return None

    # --- Methoden zum Erstellen und Senden von "Ideales Fahren" Befehlen ---
    def _create_ideal_driving_command_string(self, turn_direction, line_skips, obstacle_flag):
        """Erstellt intern den Command String für "Ideales Fahren"."""
        if turn_direction not in ['l', 'r', '0']:
            raise ValueError("Ungültige Drehrichtung. Muss 'l', 'r' oder '0' sein.")
        if not isinstance(line_skips, int) or line_skips < 0:
            raise ValueError("Line Skips muss eine nicht-negative Ganzzahl sein.")
        if obstacle_flag not in ['0', '1']:
            raise ValueError("Obstacle Flag muss '0' oder '1' sein.")
        return f"{turn_direction},{line_skips},{obstacle_flag};"

    def send_ideal_driving_command(self, turn_direction, line_skips, obstacle_flag):
        """
        Sendet einen "Ideales Fahren" Command.
        T: 'l' (links), 'r' (rechts), '0' (kein Drehen)
        S: Anzahl der zu überspringenden Linien (integer)
        O: Hindernis-Flag ('1' für erwartet, '0' für nicht erwartet)
        """
        try:
            command_str = self._create_ideal_driving_command_string(turn_direction, line_skips, obstacle_flag)
            return self._send_and_receive_raw_command(command_str)
        except ValueError as e:
            print(f"Fehler bei der Befehlserstellung: {e}")
            return None

    def send_ideal_driving_command_chain(self, commands):
        """
        Sendet eine Kette von "Ideales Fahren" Befehlen.
        Args:
            commands (list of tuples): Eine Liste von Tripeln, z.B. [('l', 1, '1'), ('r', 2, '0')]
        """
        full_command_chain = ""
        try:
            for cmd_tuple in commands:
                full_command_chain += self._create_ideal_driving_command_string(*cmd_tuple)
            return self._send_and_receive_raw_command(full_command_chain)
        except ValueError as e:
            print(f"Fehler bei der Erstellung der Befehlskette: {e}")
            return None
        except TypeError:
            print("Fehler: 'commands' Argument muss eine Liste von Tupeln sein, z.B. [('l', 1, '1')].")
            return None


    # --- Methoden zum Senden von "Spezielle Commands" ---
    def send_turn_l_duration(self, duration_ms):
        """Sendet den speziellen Befehl "Links drehen für Dauer in Millisekunden". """
        command_str = f"0,10,{duration_ms};"
        return self._send_and_receive_raw_command(command_str)

    def send_turn_r_duration(self, duration_ms):
        """Sendet den speziellen Befehl "Rechts drehen für Dauer in ms". """
        command_str = f"0,11,{duration_ms};"
        return self._send_and_receive_raw_command(command_str)

    def send_turn_l_to_next_line(self):
        """Sendet den speziellen Befehl "Links drehen bis nächste Linie". """
        command_str = "0,20,0;"
        return self._send_and_receive_raw_command(command_str)

    def send_turn_r_to_next_line(self):
        """Sendet den speziellen Befehl "Rechts drehen bis nächste Linie". """
        command_str = "0,21,0;"
        return self._send_and_receive_raw_command(command_str)

    def send_follow_line(self):
        """Sendet den speziellen Befehl "Linie folgen". """
        command_str = "0,50,0;"
        return self._send_and_receive_raw_command(command_str)

    def send_drive_backwards(self):
        """Sendet den speziellen Befehl "Vordefiniert Rückwärtsfahren". """
        command_str = "0,51,0;"
        return self._send_and_receive_raw_command(command_str)

    def send_reset_position_after_turn_to_line(self):
        """ Sendet "back;" um die Position nach "Turn L/R to next Line" zurückzusetzen."""
        command_str = "back;"
        return self._send_and_receive_raw_command(command_str)

    # --- Kontextmanager-Unterstützung ---
    def __enter__(self):
        """Für die Verwendung mit 'with' Statements."""
        if not self.is_connected:
            self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Für die Verwendung mit 'with' Statements, schließt die Verbindung."""
        self.disconnect()

# --- Hauptlogik / Beispielverwendung ---
# --- Hauptlogik / Beispielverwendung ---
if __name__ == "__main__":

    # WÄHLE DEN TESTMODUS:
    # "LOOPBACK" für den Selbsttest mit verbundenem TX und RX (GPIO14 an GPIO15)
    # "MCU" für die Kommunikation mit einem echten externen MCU
    TEST_MODE = "LOOPBACK"  # Ändere dies zu "MCU" für den normalen Betrieb

    if TEST_MODE == "LOOPBACK":
        print("****************************************************")
        print("***         STARTE UART LOOPBACK-TEST          ***")
        print("*** Stelle sicher, dass GPIO14 (TX) mit       ***")
        print("*** GPIO15 (RX) auf dem Raspberry Pi verbunden ***")
        print("*** ist! Kein externer MCU darf angeschlossen  ***")
        print("*** sein.                                      ***")
        print("****************************************************\n")

        # Für Loopback verwenden wir denselben Port, typischerweise /dev/serial0
        loopback_port = '/dev/serial0'
        # Baudrate und Timeout sind für Loopback weniger kritisch, aber konsistent halten
        loopback_baud = 9600
        loopback_timeout = 1.0 # Antwort sollte sofort kommen

        try:
            with MCUCommunicator(port=loopback_port, baudrate=loopback_baud, timeout=loopback_timeout) as mcu_lb:
                if not mcu_lb.is_connected:
                    print(f"Loopback: Verbindung auf {loopback_port} fehlgeschlagen. Programm wird beendet.")
                    exit()
                else:
                    print(f"Loopback: Verbindung auf {loopback_port} erfolgreich hergestellt.")

                # Test 1: Einfacher roher Befehl
                # Erwartung: Der gesendete Befehl wird direkt wieder empfangen.
                cmd_to_send1 = "test,loop,1;"
                print(f"\nLoopback Test 1: Sende '{cmd_to_send1}'")
                response1 = mcu_lb._send_and_receive_raw_command(cmd_to_send1)

                if response1 == cmd_to_send1:
                    print(f"Loopback Test 1 ERFOLGREICH: Empfangen '{response1}'")
                else:
                    print(f"Loopback Test 1 FEHLGESCHLAGEN: Erwartet '{cmd_to_send1}', Empfangen '{response1}'")
                    # Puffer leeren für nächsten Test, falls etwas unerwartet empfangen wurde
                    if mcu_lb.ser and mcu_lb.ser.in_waiting > 0:
                        mcu_lb.ser.read(mcu_lb.ser.in_waiting) # Lese und verwerfe verbleibende Bytes

                time.sleep(0.5)

                # Test 2: "Ideales Fahren" Einzelbefehl
                # Die Methode send_ideal_driving_command erstellt "l,0,0;"
                print("\nLoopback Test 2: Sende 'Ideal Driving Command' ('l', 0, '0')")
                expected_cmd2 = "l,0,0;"
                response2 = mcu_lb.send_ideal_driving_command('l', 0, '0')
                if response2 == expected_cmd2:
                    print(f"Loopback Test 2 ERFOLGREICH: Empfangen '{response2}'")
                else:
                    print(f"Loopback Test 2 FEHLGESCHLAGEN: Erwartet '{expected_cmd2}', Empfangen '{response2}'")
                    if mcu_lb.ser and mcu_lb.ser.in_waiting > 0:
                        mcu_lb.ser.read(mcu_lb.ser.in_waiting)

                time.sleep(0.5)

                # Test 3: "Ideales Fahren" Befehlskette
                # WICHTIG: _send_and_receive_raw_command liest nur bis zum ERSTEN Semikolon.
                # Daher wird bei einer Kette nur der erste Befehl der Kette als Antwort erwartet.
                print("\nLoopback Test 3: Sende 'Ideal Driving Command Chain'")
                ideal_commands_lb = [
                    ('r', 1, '1'), # Dieser wird gesendet und als erster Teil der Antwort erwartet
                    ('0', 2, '0'), # Dieser wird auch gesendet, aber nicht sofort gelesen
                    ('l', 0, '1')  # Dieser wird auch gesendet, aber nicht sofort gelesen
                ]
                # Der erste Befehl in der Kette ist 'r,1,1;'
                expected_cmd3_first_part = "r,1,1;"
                # Die gesamte gesendete Kette wird "r,1,1;0,2,0;l,0,1;" sein
                full_chain_sent = "r,1,1;0,2,0;l,0,1;"

                response3 = mcu_lb.send_ideal_driving_command_chain(ideal_commands_lb)

                if response3 == expected_cmd3_first_part:
                    print(f"Loopback Test 3 ERFOLGREICH: Erster Teil der Kette empfangen '{response3}'")
                    # Der Rest der Kette ("0,2,0;l,0,1;") sollte noch im Eingangspuffer sein.
                    # Wir können versuchen, ihn manuell zu lesen.
                    if mcu_lb.ser and mcu_lb.ser.in_waiting > 0:
                        time.sleep(0.1) # Kleine Pause um sicherzustellen, dass alles da ist
                        remaining_bytes = mcu_lb.ser.read(mcu_lb.ser.in_waiting)
                        remaining_str = remaining_bytes.decode('utf-8').strip()
                        expected_remaining = "0,2,0;l,0,1;" # Was wir erwarten, was noch im Puffer ist
                        print(f"Loopback Test 3: Rest im Puffer: '{remaining_str}'")
                        if remaining_str == expected_remaining:
                             print("Loopback Test 3: Restlicher Teil der Kette korrekt im Puffer gefunden.")
                        else:
                             print(f"Loopback Test 3: FEHLER beim restlichen Teil. Erwartet '{expected_remaining}', gefunden '{remaining_str}'")
                    else:
                        print("Loopback Test 3: Kein weiterer Teil der Kette im Puffer gefunden (unerwartet).")
                else:
                    print(f"Loopback Test 3 FEHLGESCHLAGEN: Erster Teil der Kette. Erwartet '{expected_cmd3_first_part}', Empfangen '{response3}'")
                    if mcu_lb.ser and mcu_lb.ser.in_waiting > 0:
                        mcu_lb.ser.read(mcu_lb.ser.in_waiting)

                time.sleep(0.5)

                # Test 4: Ein Spezialbefehl
                print("\nLoopback Test 4: Sende 'Spezialbefehl' (Links drehen für 100ms)")
                # send_turn_l_duration(100) generiert "0,10,100;"
                expected_cmd4 = "0,10,100;"
                response4 = mcu_lb.send_turn_l_duration(100)
                if response4 == expected_cmd4:
                    print(f"Loopback Test 4 ERFOLGREICH: Empfangen '{response4}'")
                else:
                    print(f"Loopback Test 4 FEHLGESCHLAGEN: Erwartet '{expected_cmd4}', Empfangen '{response4}'")
                    if mcu_lb.ser and mcu_lb.ser.in_waiting > 0:
                        mcu_lb.ser.read(mcu_lb.ser.in_waiting)

                print("\nLoopback-Tests abgeschlossen.")

        except serial.SerialException as e:
            print(f"Loopback: Kritischer Fehler mit der seriellen Schnittstelle: {e}")
        except Exception as e:
            print(f"Loopback: Ein unerwarteter Fehler ist aufgetreten: {e}")

        print("\n****************************************************")
        print("***          LOOPBACK-TEST BEENDET             ***")
        print("*** Entferne die Kabelverbindung GPIO14-GPIO15 ***")
        print("*** bevor du mit einem echten MCU testest!     ***")
        print("****************************************************")


    elif TEST_MODE == "MCU":
        print("****************************************************")
        print("***       STARTE MCU KOMMUNIKATIONSTEST        ***")
        print("*** Stelle sicher, dass der MCU korrekt         ***")
        print("*** angeschlossen und bereit ist.              ***")
        print("****************************************************\n")
        # Dein ursprünglicher Code für den MCU-Test:
        try:
            with MCUCommunicator(port='/dev/serial0', baudrate=9600, timeout=3.0) as mcu: # Port anpassen falls nötig
                if not mcu.is_connected:
                    print("MCU konnte nicht verbunden werden. Programm wird beendet.")
                    exit()

                print("\n--- Teste 'Ideales Fahren' Befehlskette ---")
                ideal_commands = [
                    ('l', 1, '1'),
                    ('r', 2, '0'),
                    ('l', 2, '1')
                ]
                response = mcu.send_ideal_driving_command_chain(ideal_commands)
                if response == "end;":
                    print("MCU hat die Befehlskette erfolgreich beendet.")
                elif response == "unknown;":
                    print("MCU hat einen unbekannten Befehl in der Kette empfangen.")
                elif response == "obstructed;":
                    print("MCU hat ein Hindernis während der idealen Fahrt erkannt.")
                elif response:
                    print(f"Unerwartete Antwort von idealer Fahrt: {response}")
                else: # response ist None oder leer
                    print("Keine oder ungültige Antwort von idealer Fahrt.")


                time.sleep(1)

                print("\n--- Teste Spezialbefehle ---")
                print("\nSende: Links drehen für 500ms")
                response = mcu.send_turn_l_duration(500)
                if response == "end;":
                    print("Links drehen beendet.")
                else:
                    print(f"Antwort auf Links drehen: {response if response else 'Keine Antwort'}")

                time.sleep(1)

                print("\nSende: Linie folgen")
                response = mcu.send_follow_line()
                if response == "obstructed;":
                    print("Hindernis beim Linienfolgen erkannt!")
                elif response == "end;":
                    print("Linienfolgen beendet.")
                else:
                    print(f"Antwort auf Linie folgen: {response if response else 'Keine Antwort'}")

                time.sleep(1)

                print("\nSende: Rechts drehen bis zur nächsten Linie")
                response = mcu.send_turn_r_to_next_line()
                if response == "end;":
                    print("Nächste Linie rechts erreicht.")
                elif response == "obstructed;":
                    print("Hindernis beim Drehen zur nächsten Linie rechts.")
                else:
                    print(f"Antwort auf Rechts drehen zu Linie: {response if response else 'Keine Antwort'}")

        except serial.SerialException as e:
            print(f"MCU-Test: Kritischer Fehler mit der seriellen Schnittstelle: {e}")
        except Exception as e:
            print(f"MCU-Test: Ein unerwarteter Fehler ist aufgetreten: {e}")

    else:
        print(f"Unbekannter TEST_MODE: {TEST_MODE}. Wähle 'LOOPBACK' oder 'MCU'.")


    print("\nProgramm beendet.")