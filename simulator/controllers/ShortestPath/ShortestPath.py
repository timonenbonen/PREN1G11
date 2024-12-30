from controller import Supervisor
import json

# Initialize Supervisor
supervisor = Supervisor()

# Load the JSON file containing the shortest path
with open("../GraphGenerator/shortest_path.json") as f:
    shortest_path = json.load(f)


# Function to find a node by DEF name
def get_node_by_def(def_name):
    return supervisor.getFromDef(def_name)


# Function to change the color of a node
def set_node_color(node, color):
    if node is None:
        print(f"Node not found.")
        return
    try:
        children_field = node.getField("children")
        shape_node = children_field.getMFNode(0)  # First child is Shape
        appearance_field = shape_node.getField("appearance")
        pbr_node = appearance_field.getSFNode()  # Access PBRAppearance
        base_color_field = pbr_node.getField("baseColor")

        # Validate and set color
        if len(color) != 3 or not all(isinstance(c, (int, float)) for c in color):
            raise ValueError("Color must be a tuple of three floats.")
        base_color_field.setSFVec3f(color)
        print(f"Node color updated successfully: {color}")
    except Exception as e:
        print(f"Error updating node color: {e}")


# Get simulation time step
time_step = int(supervisor.getBasicTimeStep())

# Update colors for nodes in the shortest path
for node in shortest_path["nodes"]:
    for name, position in node.items():
        target_node = get_node_by_def(name)  # Find node by DEF name
        if target_node:
            set_node_color(target_node, [0.0, 1.0, 0.0])  # Change color to green (shortest path)
        else:
            print(f"Node with DEF name '{name}' not found.")

    # Advance simulation for 2 seconds to visualize the change
    for _ in range(int(2 * 1000 / time_step)):  # Convert 2 seconds to simulation steps
        supervisor.step(time_step)
