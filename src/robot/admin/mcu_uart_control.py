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
if __name__ == "__main__":
    # Erstelle eine Instanz des MCUCommunicators
    # Passe Port, Baudrate und Timeout bei Bedarf an
    # Für Windows wäre der Port z.B. 'COM3'
    # Für Raspberry Pi typischerweise '/dev/ttyS0' oder '/dev/serial0'
    # Für Linux allgemein oft '/dev/ttyUSB0' oder '/dev/ttyACM0' für USB-Seriell-Adapter

    # Verwendung mit 'with'-Statement (empfohlen, da es das disconnect() automatisch handhabt)
    try:
        with MCUCommunicator(port='/dev/serial0', baudrate=9600, timeout=3.0) as mcu:
            if not mcu.is_connected:
                print("MCU konnte nicht verbunden werden. Programm wird beendet.")
                exit()

            print("\n--- Teste 'Ideales Fahren' Befehlskette ---")
            # Beispiel: "l,1,1;r,2,0;l,2,1;"
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

            time.sleep(1) # Kurze Pause zwischen den Testsequenzen

            print("\n--- Teste Spezialbefehle ---")

            # Beispiel: Links drehen für 500ms
            print("\nSende: Links drehen für 500ms")
            response = mcu.send_turn_l_duration(500)
            # Hier die Antwort verarbeiten, z.B. auf "end;" warten
            if response == "end;":
                print("Links drehen beendet.")
            else:
                print(f"Antwort auf Links drehen: {response}")

            time.sleep(1)

            # Beispiel: Linie folgen
            print("\nSende: Linie folgen")
            response = mcu.send_follow_line()
            if response == "obstructed;":
                print("Hindernis beim Linienfolgen erkannt!")
                # Laut Doku: "The MCU awaits instructions from the raspy."
                # Hier könnte man z.B. zurückfahren:
                # print("Sende: Rückwärts fahren nach Hindernis")
                # response_back = mcu.send_drive_backwards()
                # print(f"Antwort auf Rückwärtsfahren: {response_back}")
            elif response == "end;":
                 print("Linienfolgen beendet.")
            else:
                print(f"Antwort auf Linie folgen: {response}")

            time.sleep(1)

            # Beispiel: Rechts drehen bis zur nächsten Linie
            print("\nSende: Rechts drehen bis zur nächsten Linie")
            response = mcu.send_turn_r_to_next_line()
            if response == "end;": # Oder eine andere Bestätigung, dass die Linie erreicht wurde
                print("Nächste Linie rechts erreicht.")
                # Laut Doku: "Send "back;" to reset position."
                # print("Sende: 'back;' um Position zurückzusetzen")
                # reset_response = mcu.send_reset_position_after_turn_to_line()
                # print(f"Antwort auf 'back;': {reset_response}")
            elif response == "obstructed;":
                print("Hindernis beim Drehen zur nächsten Linie rechts.")
            else:
                print(f"Antwort auf Rechts drehen zu Linie: {response}")


            # Beispiel: Unbekannter Befehl (manuell gesendet, nicht über eine Methode)
            # print("\n--- Teste unbekannten Befehl ---")
            # unknown_command_str = "X,Y,Z;"
            # response = mcu._send_and_receive_raw_command(unknown_command_str) # Nutze die private Methode für rohe Befehle
            # if response == "unknown;":
            #     print("MCU hat den unbekannten Befehl korrekt als 'unknown;' gemeldet.")
            # else:
            #     print(f"Antwort auf unbekannten Befehl: {response}")


    except serial.SerialException as e:
        print(f"Kritischer Fehler mit der seriellen Schnittstelle: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

    print("\nProgramm beendet.")