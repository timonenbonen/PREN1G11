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

    edges = {
        "E_F": Box(name="E_F", node1=nodes['E'], node2=nodes['F']),
        "E_D": Box(name="E_D", node1=nodes['E'], node2=nodes['D']),
        "E_G": Box(name="E_G", node1=nodes['E'], node2=nodes['G']),
        "D_A": Box(name="D_A", node1=nodes['D'], node2=nodes['A']),
        "D_G": Box(name="D_G", node1=nodes['D'], node2=nodes['G']),
        "A_B": Box(name="A_B", node1=nodes['A'], node2=nodes['B']),
        "A_H": Box(name="A_H", node1=nodes['A'], node2=nodes['H']),
        "A_G": Box(name="A_G", node1=nodes['A'], node2=nodes['G']),
        "B_C": Box(name="B_C", node1=nodes['B'], node2=nodes['C']),
        "B_H": Box(name="B_H", node1=nodes['B'], node2=nodes['H']),
        "C_H": Box(name="C_H", node1=nodes['C'], node2=nodes['H']),
        "C_F": Box(name="C_F", node1=nodes['C'], node2=nodes['F']),
        "F_H": Box(name="F_H", node1=nodes['F'], node2=nodes['H']),
        "F_G": Box(name="F_G", node1=nodes['F'], node2=nodes['G']),
        "H_G": Box(name="H_G", node1=nodes['H'], node2=nodes['G'])
    }

    return nodes, edges