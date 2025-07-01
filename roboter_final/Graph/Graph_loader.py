# graph_loader.py

from typing import Dict, Tuple
from roboter_final.Graph.Cylinder import Cylinder
from roboter_final.Graph.Box import Box
import json
from typing import cast
import os
# You can also use a JSON file for this, but Python dicts give more flexibility.

# Position constants
node_middle_x = 0.0
node_bottom_y = 0.0
node_left_x = -1.0
node_right_x = 1.0
node_middle_y = 1.0
node_between_x = 0.5
node_side_top_y = 2.0
node_side_bottom_y = 0.5
node_top_y = 3.0
script_dir = os.path.dirname(__file__)
file_path = os.path.join(script_dir, 'graph_data.json')

def load_nodes_and_edges() -> Tuple[Dict[str, Cylinder], Dict[str, Box]]:
    with open(file_path, 'r') as f:
        data = json.load(f)

    node_positions = data["nodes"]
    nodes = {
        name: Cylinder(name=name, position_x_y=cast(tuple[float, float], tuple(pos)))
        for name, pos in node_positions.items()
    }

    # Define original edges
    raw_edges = [
        ("E", "F"),
        ("E", "D"),
        ("E", "G"),
        ("D", "A"),
        ("D", "G"),
        ("A", "B"),
        ("A", "H"),
        ("A", "G"),
        ("B", "C"),
        ("B", "H"),
        ("C", "H"),
        ("C", "F"),
        ("F", "H"),
        ("F", "G"),
        ("H", "G"),
    ]

    edges: Dict[str, Box] = {}

    for node1, node2 in raw_edges:
        key1 = f"{node1}_{node2}"
        key2 = f"{node2}_{node1}"

        # Create edge in both directions
        edges[key1] = Box(name=key1, node1=nodes[node1], node2=nodes[node2])
        edges[key2] = Box(name=key2, node1=nodes[node2], node2=nodes[node1])

    return nodes, edges