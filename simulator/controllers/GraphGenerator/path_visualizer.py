from controller import Supervisor
import json

# Initialize Supervisor
supervisor = Supervisor()

# Load the JSON file containing the shortest path
with open("shortest_path.json") as f:
    shortest_path = json.load(f)

# Function to find a node by DEF name
def get_node_by_def(def_name):
    return supervisor.getFromDef(def_name)

# Function to change the color of a node
def set_node_color(node, color):
    if node:
        shape_node = node.getField("children").getMFNode(0)  # Get the Shape node
        appearance_field = shape_node.getField("appearance")
        appearance_node = appearance_field.getSFNode()
        color_field = appearance_node.getField("baseColor")
        color_field.setSFVec3f(color)  # Set new color (RGB)

# Update colors for nodes in the shortest path
for node in shortest_path["nodes"]:
    for name, position in node.items():
        target_node = get_node_by_def(name)  # Find node by DEF name
        set_node_color(target_node, (0, 1, 0))  # Change color to green (shortest path)

# Start simulation steps to apply changes
supervisor.step(int(supervisor.getBasicTimeStep()))
