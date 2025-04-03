def calculate_path(graph_data):
    print(f"[PathCalculation] Calculating path from {graph_data['start']} to {graph_data['end']}")
    if graph_data["start"] == "A":
        return ["A", "C", "D", "B"]  # dummy path
    return None