import numpy as np

# Finale Koordinaten
positions = {
    0: [100, 100],  # A
    1: [200, 50],  # B
    2: [300, 100],  # C
    3: [300, 200],  # D
    4: [194, 250],  # E
    5: [100, 200],  # F
    6: [196, 185],  # G
    7: [179, 133]  # H
}

labels = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']

# Roboter-Navigationsregeln: Welcher Punkt ist das nächste Ziel von jedem Punkt
next_targets = {
    4: 6,  # E -> G
    3: 2,  # D -> C
    6: 7,  # G -> H
    5: 0,  # F -> A
    2: 1,  # C -> B
    7: 1,  # H -> B
    0: 1,  # A -> B
    1: 7  # B -> H
}


def calculate_robot_turn(from_label, to_label, current_heading_deg=0):
    """
    Berechnet beide Drehungen des Roboters:
    1. Drehung zum Ziel (von aktueller Ausrichtung)
    2. Drehung zum nächsten Ziel (nach Ankunft)

    Args:
        from_label: Startpunkt (z.B. 'E')
        to_label: Zielpunkt (z.B. 'D')
        current_heading_deg: Aktuelle Ausrichtung des Roboters in Grad (0° = rechts/Osten)
    """
    # Labels zu Indizes konvertieren
    try:
        from_idx = labels.index(from_label)
        to_idx = labels.index(to_label)
    except ValueError:
        return f"Fehler: Ungültiger Punkt"

    # Nächstes Ziel nach dem aktuellen Ziel bestimmen
    if to_idx not in next_targets:
        return f"Fehler: Kein nächstes Ziel für Punkt {to_label}"

    next_idx = next_targets[to_idx]
    next_label = labels[next_idx]

    # Koordinaten holen
    from_pos = np.array(positions[from_idx])
    to_pos = np.array(positions[to_idx])
    next_pos = np.array(positions[next_idx])

    # Richtungsvektoren berechnen
    to_direction = to_pos - from_pos  # Richtung von FROM zu TO
    next_direction = next_pos - to_pos  # Richtung von TO zu NEXT

    # Winkel berechnen
    to_angle = np.arctan2(to_direction[1], to_direction[0])
    next_angle = np.arctan2(next_direction[1], next_direction[0])

    # 1. Drehung: Von aktueller Ausrichtung zum Ziel
    current_heading_rad = np.radians(current_heading_deg)
    turn_to_target = to_angle - current_heading_rad

    # Winkel normalisieren
    if turn_to_target > np.pi:
        turn_to_target -= 2 * np.pi
    elif turn_to_target < -np.pi:
        turn_to_target += 2 * np.pi

    turn_to_target_deg = np.degrees(turn_to_target)

    # 2. Drehung: Vom Ziel zum nächsten Punkt
    turn_to_next = next_angle - to_angle

    # Winkel normalisieren
    if turn_to_next > np.pi:
        turn_to_next -= 2 * np.pi
    elif turn_to_next < -np.pi:
        turn_to_next += 2 * np.pi

    turn_to_next_deg = np.degrees(turn_to_next)

    # Formatierung der Ausgabe
    def format_turn(angle_deg):
        if abs(angle_deg) < 0.1:
            return "GERADEAUS"
        elif angle_deg > 0:
            return f"LINKS {angle_deg:.1f}°"
        else:
            return f"RECHTS {abs(angle_deg):.1f}°"

    turn1 = format_turn(turn_to_target_deg)
    turn2 = format_turn(turn_to_next_deg)

    return f"{from_label}→{to_label}→{next_label}: 1) {turn1}, 2) {turn2}"


# Beispiele
if __name__ == "__main__":
    # Standard: Roboter schaut nach rechts (0°)
    print("Standard (Roboter schaut nach rechts, 0°):")
    print(calculate_robot_turn('E', 'D'))
    print(calculate_robot_turn('A', 'B'))
    print(calculate_robot_turn('B', 'H'))

    print("\nMit anderer Startausrichtung (90° = nach oben):")
    print(calculate_robot_turn('E', 'D', 90))
    print(calculate_robot_turn('A', 'B', 90))