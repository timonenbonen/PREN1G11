from typing import Dict

from roboter_final.Graph.Cylinder import Cylinder
from roboter_final.Graph.Box import Box
import heapq
from roboter_final.Graph import Graph_loader

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
max_graph_size: float = canvas_size / 1.25
min_length: float = max_graph_size / 9
max_length: float = min_length * 4
min_orientation_diff: float = 5
canvas_webots_relation: float = 4.5 / max_graph_size
max_velocity_in_ms: float = 0.5
acceleration_in_ms2: float = 1.0
breaking_speed_in_ms2: float = 2.0
align_time_in_ms: float = 1


class Graph:
    def __init__(self, target_node: str, current_node: Cylinder = None, nodes: Dict[str, Cylinder] = None,
                 edges: Dict[str, Box] = None):
        if nodes is None or edges is None:
            nodes, edges = Graph_loader.load_nodes_and_edges()
        if current_node is None:
            self.current_node_node = nodes["E"]
        self.nodes: Dict[str, Cylinder] = nodes  # {node_id: (x, y)}
        self.edges: Dict[str, Box] = edges
        self.target_node: Cylinder = nodes[target_node]  # Target node IDs
        self.current_node: Cylinder = current_node
        self.possible_target_nodes: list[Cylinder] = [nodes['F'], nodes['G'], nodes['H']]

    def change_target(self, new_target_node) -> None:
        self.target_node = new_target_node

    def set_current_node(self, new_node:str) -> None:
        self.current_node = self.nodes[new_node]

    def get_edges(self) -> Dict[str, Box]:
        return self.edges

    def mirror_y_axis(self, coordination_system_size: float = canvas_size) -> None:
        for cylinder in self.nodes.values():
            cylinder.mirror_y_axis(coordination_system_size)

    def scale_graph(self, scaling_factor: float) -> None:
        for cylinder in self.nodes.values():
            old_coordinates: tuple[float, float] = cylinder.get_x_y()
            cylinder.set_x_y(old_coordinates[0] * scaling_factor, old_coordinates[1] * scaling_factor)

    def calculate_size(self) -> tuple[float, float]:
        """
        Calculate the size of the graph in terms of width and height.

        :return: A tuple (width, height) representing the graph's dimensions.
        """
        if not self.nodes:
            return 0.0, 0.0

        # Get all x and y coordinates from the nodes
        x_coords = [node.get_x_y()[0] for node in self.nodes.values()]
        y_coords = [node.get_x_y()[1] for node in self.nodes.values()]

        # Calculate width and height
        width = max(x_coords) - min(x_coords)
        height = max(y_coords) - min(y_coords)

        return width, height

    def calculate_shortest_path(self, max_velocity_in_ms: float = max_velocity_in_ms, acceleration_in_ms2: float = acceleration_in_ms2,
                                breaking_speed_in_ms2: float = breaking_speed_in_ms2, align_time_in_s:float = align_time_in_ms) -> tuple[list, list]:
        """
        Calculates the shortest path between starting_node and target_node using Dijkstra's algorithm.

        :return: A list alternating between node IDs and edge IDs in the shortest path order.
        """
        # Create adjacency list, skipping blocked nodes
        adjacency_list: dict[str, list] = {node: [] for node in self.nodes if not self.nodes[node].is_blocked}
        for edge_id, edge in self.edges.items():
            if not edge.is_removed:  # Ignore removed edges
                node1: str = edge.node1.get_name()
                node2: str = edge.node2.get_name()
                if not edge.node1.is_blocked and not edge.node2.is_blocked:  # Skip edges connected to blocked nodes
                    time_to_traverse = edge.calculate_traversal_time_edge(max_speed=max_velocity_in_ms,
                                                                          acceleration=acceleration_in_ms2,
                                                                          braking_speed=breaking_speed_in_ms2,
                                                                          align_time=align_time_in_s)  # Get length of the edge
                    adjacency_list[node1].append((node2, time_to_traverse))
                    adjacency_list[node2].append((node1, time_to_traverse))
        print(self.current_node)
        # Dijkstra's algorithm setup
        priority_queue = [(0, self.current_node.get_name(), [])]  # (distance, current_node, path_so_far)
        visited = set()
        algorithm_sequence = []

        while priority_queue:
            current_distance, current_node, path = heapq.heappop(priority_queue)

            if current_node in visited:
                continue

            visited.add(current_node)
            edge_name: str = ""
            # Add the current node to the path
            if path:
                # Add the edge name between the last node in the path and the current node
                last_node = path[-1]
                edge_name = f"{last_node}_{current_node}"
                if edge_name not in self.edges:
                    edge_name = f"{current_node}_{last_node}"  # Check reversed edge
                algorithm_sequence.append(edge_name)
            algorithm_sequence.append(current_node)

            path = path + [edge_name] + [current_node] if path else [current_node]

            # If target node is reached, return the path with edges
            if current_node == self.target_node.get_name():
                print(algorithm_sequence,path)
                return algorithm_sequence, path

            # Explore neighbors
            for neighbor, weight in adjacency_list.get(current_node, []):
                if neighbor not in visited:
                    heapq.heappush(priority_queue, (current_distance + weight, neighbor, path))

        # If no path is found, return an empty list
        return [], []

    def get_first_edge_in_shortest_path(self) -> str | None:
        if self.current_node.get_name() == self.target_node.get_name():
            return None

        _, path = self.calculate_shortest_path()
        return path[1] if len(path) >= 2 else None

    def block_edge(self, edge_name: str) -> None:
        node1, node2 = edge_name.split("_")
        reverse_name = f"{node2}_{node1}"
        if edge_name in self.edges:
            self.edges[edge_name].set_has_obstacle(True)
        if reverse_name in self.edges:
            self.edges[reverse_name].set_has_obstacle(True)

    def remove_edge(self, edge_name: str) -> None:
        node1, node2 = edge_name.split("_")
        reverse_name = f"{node1}_{node2}"
        if edge_name in self.edges:
            self.edges[edge_name].set_is_removed(True)
            print("removing edge worked")
            print(self.edges[edge_name].is_removed)
        else:
            print("removing edge error")
        if reverse_name in self.edges:
            self.edges[reverse_name].set_is_removed(True)
            print(self.edges[reverse_name].is_removed)
            print("removing edge worked")
        else:
            print("removing edge error")
