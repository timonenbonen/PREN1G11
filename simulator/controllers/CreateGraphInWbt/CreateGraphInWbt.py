from Box import Box
from Cylinder import Cylinder
from SetWebotsColor import SetWebotsColor
from CanvasInterface import CanvasInterface
from Graph import Graph
from controller import Supervisor
import pickle
from Roboter import Roboter
# Global Constants
canvas_size = 800
relation_height_length = 330 / 280

half_canvas = canvas_size / 2
quarter_canvas = canvas_size / 4
three_quarters_canvas = canvas_size * 3 / 4
height_diff = (quarter_canvas - three_quarters_canvas) / 4

node_middle_y = half_canvas
node_middle_x = half_canvas
node_bottom_y = three_quarters_canvas
node_top_y = quarter_canvas
node_left_x = node_middle_x - quarter_canvas / relation_height_length
node_right_x = node_middle_x + quarter_canvas / relation_height_length
node_side_bottom_y = three_quarters_canvas + height_diff
node_side_top_y = quarter_canvas - height_diff
node_between_x = node_left_x + (node_right_x - node_left_x) / 4

nodes: dict[str, Cylinder] = {
    'A': Cylinder(name='A', position_x_y=(node_middle_x, node_bottom_y)),
    'B': Cylinder(name='B', position_x_y=(node_left_x, node_side_bottom_y)),
    'C': Cylinder(name='C', position_x_y=(node_right_x, node_side_bottom_y)),
    'D': Cylinder(name='D', position_x_y=(node_middle_x, node_middle_y)),
    'E': Cylinder(name='E', position_x_y=(node_between_x, node_side_top_y)),
    'F': Cylinder(name='F', position_x_y=(node_left_x, node_side_top_y)),
    'G': Cylinder(name='G', position_x_y=(node_right_x, node_side_top_y)),
    'H': Cylinder(name='H', position_x_y=(node_middle_x, node_top_y))
}

edges: dict[str, Box] = {
    "A_B": Box(name="A_B", node1=nodes['A'], node2=nodes['B']),
    "A_C": Box(name="A_C", node1=nodes['A'], node2=nodes['C']),
    "A_D": Box(name="A_D", node1=nodes['A'], node2=nodes['D']),
    "B_D": Box(name="B_D", node1=nodes['B'], node2=nodes['D']),
    "B_F": Box(name="B_F", node1=nodes['B'], node2=nodes['F']),
    "B_E": Box(name="B_E", node1=nodes['B'], node2=nodes['E']),
    "C_D": Box(name="C_D", node1=nodes['C'], node2=nodes['D']),
    "C_G": Box(name="C_G", node1=nodes['C'], node2=nodes['G']),
    "D_E": Box(name="D_E", node1=nodes['D'], node2=nodes['E']),
    "D_G": Box(name="D_G", node1=nodes['D'], node2=nodes['G']),
    "E_F": Box(name="E_F", node1=nodes['E'], node2=nodes['F']),
    "E_G": Box(name="E_G", node1=nodes['E'], node2=nodes['G']),
    "E_H": Box(name="E_H", node1=nodes['E'], node2=nodes['H']),
    "F_H": Box(name="F_H", node1=nodes['F'], node2=nodes['H']),
    "H_G": Box(name="H_G", node1=nodes['H'], node2=nodes['G'])
}
possible_target_nodes: list[Cylinder] = [nodes['F'], nodes['G'], nodes['H']]


max_graph_size: float = canvas_size / 1.25
min_length: float = max_graph_size / 9
max_length: float = min_length * 4
min_orientation_diff: float = 5
canvas_webots_relation: float = 4.5 / max_graph_size
max_velocity_in_ms: float = 0.5
acceleration_in_ms2: float = 1.0
breaking_speed_in_ms2: float = 2.0
align_time_in_ms: float = 1

if __name__ == "__main__":
    graph = Graph(
        starting_node=nodes['A'],
        target_node=nodes['H'],
        nodes=nodes,
        edges=edges
    )
    editor = CanvasInterface(graph=graph, canvas_size=canvas_size, possible_target_nodes = possible_target_nodes, canvas_webots_relation=canvas_webots_relation)
    editor.run_loop()
    graph.mirror_y_axis(canvas_size)
    graph.scale_graph(canvas_webots_relation)

    vrml_graph: list[str] = graph.to_vrml()
    # Initialize Supervisor
    supervisor = Supervisor()
    # Get the root node and its children field
    root_node = supervisor.getRoot()
    children_field = root_node.getField('children')
    # Import the generated VRML from the PoseNode object
    for element in vrml_graph:
        if element.strip():
            children_field.importMFNodeFromString(-1, element)
    time_step = int(supervisor.getBasicTimeStep())
    while supervisor.step(time_step) != -1:
        # Shortest path calculation
        shortest_path_algorithm, path = graph.calculate_shortest_path(max_velocity_in_ms = max_velocity_in_ms, acceleration_in_ms2 = acceleration_in_ms2,
                                breaking_speed_in_ms2 = breaking_speed_in_ms2, align_time_in_s = 1.0)

        # Set Webots colors
        SetWebotsColor.set_webots_color(webots_names=shortest_path_algorithm, supervisor=supervisor, step_time_ms=500)
        SetWebotsColor.set_webots_color(webots_names=path, supervisor=supervisor, color=[1.0, 1.0, 0])
        roboter = Roboter(supervisor, graph, max_velocity_in_ms = max_velocity_in_ms, acceleration_in_ms2 = acceleration_in_ms2,
                                breaking_speed_in_ms2 = breaking_speed_in_ms2, align_time_in_s = 1.0)
        roboter.traverse_graph(supervisor, path)
        break