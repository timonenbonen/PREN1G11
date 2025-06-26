# graph_loader.py

from typing import Dict, Tuple
from Cylinder import Cylinder
from Box import Box
import json
from typing import cast
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

def load_nodes_and_edges() -> Tuple[Dict[str, Cylinder], Dict[str, Box]]:
    with open("graph_data.json", 'r') as f:
        data = json.load(f)

    node_positions = data["nodes"]
    nodes = {
        name: Cylinder(name=name, position_x_y=cast(tuple[float, float], tuple(pos)))
        for name, pos in node_positions.items()
    }

    edges = {
        "E_F": Box(name="E_F", node1=nodes['E'], node2=nodes['F']),
        "E_D": Box(name="E_D", node1=nodes['E'], node2=nodes['D']),
        "E_G": Box(name="E_G", node1=nodes['E'], node2=nodes['G']),
        "D_C": Box(name="D_C", node1=nodes['D'], node2=nodes['C']),
        "D_G": Box(name="D_G", node1=nodes['D'], node2=nodes['G']),
        "C_B": Box(name="C_B", node1=nodes['C'], node2=nodes['B']),
        "C_H": Box(name="C_H", node1=nodes['C'], node2=nodes['H']),
        "C_G": Box(name="C_G", node1=nodes['C'], node2=nodes['G']),
        "B_A": Box(name="B_A", node1=nodes['B'], node2=nodes['A']),
        "B_H": Box(name="B_H", node1=nodes['B'], node2=nodes['H']),
        "A_H": Box(name="A_H", node1=nodes['A'], node2=nodes['H']),
        "A_F": Box(name="A_F", node1=nodes['A'], node2=nodes['F']),
        "F_H": Box(name="F_H", node1=nodes['F'], node2=nodes['H']),
        "F_G": Box(name="F_G", node1=nodes['F'], node2=nodes['G']),
        "H_G": Box(name="H_G", node1=nodes['H'], node2=nodes['G'])
    }

    return nodes, edges
