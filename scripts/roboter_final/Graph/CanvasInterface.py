import tkinter as tk
import Graph
import Cylinder
import Box
import math
import json
from typing import Any

class CanvasInterface:
    def __init__(self, graph: Graph, canvas_size: float, possible_target_nodes: list[Cylinder], canvas_webots_relation:float):
        self.root: tk.Tk = tk.Tk()
        self.graph = graph
        self.possible_target_nodes = possible_target_nodes
        self.canvas_webots_relation = canvas_webots_relation
        # Canvas setup
        self.canvas: tk.Canvas = tk.Canvas(self.root, width=canvas_size, height=canvas_size, bg="white")
        self.canvas.pack(side=tk.LEFT)
        self.min_length = 0.5
        self.max_length = 2.0
        self.min_angle = 10.0
        self.max_graph_size = 4.0 / canvas_webots_relation # Maximum graph size

        self.node_radius: float = 10
        self.selected_node = None
        self.hovered_edge = None
        self.node_shapes = {}  # Maps nodes to canvas IDs
        self.edge_shapes = {}  # Maps edges to canvas IDs
        self.edge_obstacles = {}  # Maps edges to obstacle canvas IDs

        self.draw_graph()

        # Event bindings
        self.canvas.bind("<ButtonPress-1>", self.on_node_press)
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_node_release)
        self.root.bind("<o>", self.toggle_obstacle)
        self.root.bind("<b>", self.toggle_blocked_node)
        self.root.bind("<r>", self.toggle_removed_edge)
        self.root.bind("<t>", self.set_target)


        # Options list and close button
        self.options_frame = tk.Frame(self.root)
        self.options_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.options_label = tk.Label(self.options_frame, text="While hovering over the graph\nyou have the following options:\n\n"
                                                                   "- Press 'b': Toggle -node blocked-\n"
                                                                   "- Press 'r': Toggle -node removed-\n"
                                                                   "- Press 't': Set node as new target\n"
                                                                   "- Press 'o': Toggle obstacle on edge",
                                                          font=("Helvetica", 12),
                                                          justify = "left",
                                                          anchor = "nw",
                                                          bg = "white")

        self.options_label.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        self.close_button = tk.Button(
            self.root,
            text="Create Graph",
            command=self.root.destroy,
            bg="blue",
            fg="white",
            font=("Helvetica", 16),
            padx=20,
            pady=10
        )
        self.close_button.pack(side=tk.BOTTOM, pady=20)

    def draw_graph(self):
        # Draw edges
        for edge_name, edge in self.graph.edges.items():
            self.draw_edge(edge)

        # Draw nodes
        for node_name, node in self.graph.nodes.items():
            self.draw_node(node)

    def draw_node(self, node):
        x, y = node.get_x_y()
        color = 'red' if node.is_blocked else 'black'
        if node == self.graph.target_node:
            color = 'blue'
        elif node == self.graph.current_node:
            color = 'green'

        oval = self.canvas.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill=color, outline=color
        )
        self.node_shapes[node] = oval

    def draw_edge(self, edge):
        x1, y1 = edge.node1.get_x_y()
        x2, y2 = edge.node2.get_x_y()
        edge_length, angle = edge.get_length_and_angle()

        line_style = (4, 4) if edge.is_removed else None
        is_allowed_edge: bool = self.validate_edge_criteria(edge = edge)
        if is_allowed_edge:
            color = 'black'
        else:
            color = 'red'
        # Draw the edge
        line = self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2, dash=line_style)
        self.edge_shapes[edge] = line


        # Draw the obstacle if it exists
        if edge.has_obstacle and edge not in self.edge_obstacles:
            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
            obstacle_radius = 5
            obstacle = self.canvas.create_oval(
                mid_x - obstacle_radius, mid_y - obstacle_radius,
                mid_x + obstacle_radius, mid_y + obstacle_radius,
                fill="orange", outline="orange"
            )
            self.edge_obstacles[edge] = obstacle

    def on_node_press(self, event):
        for node, canvas_id in self.node_shapes.items():
            x, y = node.get_x_y()
            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                self.selected_node = node
                break

    def on_node_drag(self, event):
        if self.selected_node and self.graph.current_node is not self.selected_node:
            self.selected_node.set_x_y(event.x, event.y)
            self.canvas.coords(
                self.node_shapes[self.selected_node],
                event.x - self.node_radius, event.y - self.node_radius,
                event.x + self.node_radius, event.y + self.node_radius
            )
            self.update_edges()

    def validate_edge_criteria(self, edge, min_length: float = 0.5, max_length: float = 2, min_angle: float = 10, max_size: tuple[float, float] = ()) -> bool:
        """Check if edges meet specific criteria for length, angle, and crossing."""
        edge_length, edge_angle = edge.get_length_and_angle()
        if max(self.graph.calculate_size())>self.max_graph_size:
            return False

        # Check length criteria
        if not (min_length <= edge_length*self.canvas_webots_relation <= max_length):

            return False

        # Check angles for connected edges
        for other_edge in self.graph.edges.values():
            if other_edge == edge:
                continue


            if edge.node1 is other_edge.node1 or edge.node2 is other_edge.node2:
                _, other_angle = other_edge.get_length_and_angle()
                angle_diff = abs(math.degrees(edge_angle) - math.degrees(other_angle))
                angle_diff = min(angle_diff, 360 - angle_diff)  # Normalize angle difference

                if angle_diff < min_angle:

                    return False

        # Check for crossing edges
        for other_edge in self.graph.edges.values():
            if other_edge == edge:
                continue


        return True


    def on_node_release(self, event):
        self.selected_node = None

    def update_edges(self):
        for edge, canvas_id in self.edge_shapes.items():
            x1, y1 = edge.node1.get_x_y()
            x2, y2 = edge.node2.get_x_y()
            line_style = (4, 4) if edge.is_removed else ()
            self.canvas.coords(canvas_id, x1, y1, x2, y2)
            self.canvas.itemconfig(canvas_id, dash=line_style)

            # Update obstacle position if it exists
            if edge in self.edge_obstacles:
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                obstacle_radius = 5
                self.canvas.coords(
                    self.edge_obstacles[edge],
                    mid_x - obstacle_radius, mid_y - obstacle_radius,
                    mid_x + obstacle_radius, mid_y + obstacle_radius
                )
            self.redraw_edge(edge)

    def toggle_blocked_node(self, event):
        for node, canvas_id in self.node_shapes.items():
            x, y = node.get_x_y()
            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                if node == self.graph.target_node:

                    return
                node.change_is_blocked()
                self.redraw_node(node)
                break

    def toggle_obstacle(self, event):
        if self.is_cursor_near_edge(event):
            edge = self.is_cursor_near_edge(event)
            if edge in self.edge_obstacles:
                # Remove obstacle
                self.canvas.delete(self.edge_obstacles[edge])
                del self.edge_obstacles[edge]
                edge.has_obstacle = False
            else:
                # Add obstacle
                x1, y1 = edge.node1.get_x_y()
                x2, y2 = edge.node2.get_x_y()
                mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                obstacle_radius = 5
                obstacle = self.canvas.create_oval(
                    mid_x - obstacle_radius, mid_y - obstacle_radius,
                    mid_x + obstacle_radius, mid_y + obstacle_radius,
                    fill="orange", outline="orange"
                )
                self.edge_obstacles[edge] = obstacle
                edge.has_obstacle = True
            self.redraw_edge(edge)

    def set_target(self, event):

        for node, canvas_id in self.node_shapes.items():
            x, y = node.get_x_y()

            if (x - self.node_radius < event.x < x + self.node_radius and
                    y - self.node_radius < event.y < y + self.node_radius):
                if node not in self.possible_target_nodes:
                    return
                node.is_blocked = False
                self.graph.change_target(node)
                self.redraw_node(self.graph.nodes['F'])
                self.redraw_node(self.graph.nodes['G'])
                self.redraw_node(self.graph.nodes['H'])
                break

    def toggle_removed_edge(self, event):
        if self.is_cursor_near_edge(event):
            edge = self.is_cursor_near_edge(event)
            if edge in self.edge_obstacles:
                # Remove associated obstacle if it exists
                self.canvas.delete(self.edge_obstacles[edge])
                del self.edge_obstacles[edge]
                edge.has_obstacle = False  # Reflect the state in the object

            edge.is_removed = not edge.is_removed  # Toggle the removed state
            self.redraw_edge(edge)  # Redraw the edge



    def redraw_node(self, node):
        self.canvas.delete(self.node_shapes[node])
        self.draw_node(node)

    def redraw_edge(self, edge):
        if edge in self.edge_shapes:
            self.canvas.delete(self.edge_shapes[edge])
        self.draw_edge(edge)
        self.redraw_node(edge.node1)
        self.redraw_node(edge.node2)

    def is_point_near_line(self, px: float, py: float, x1: float, y1: float, x2: float, y2: float,
                           threshold: float = 5.0) -> bool:
        if x1 == x2 and y1 == y2:  # Special case: line is a point
            return abs(px - x1) <= threshold and abs(py - y1) <= threshold

        # Calculate perpendicular distance from point to line
        distance = abs((y2 - y1) * px - (x2 - x1) * py + x2 * y1 - y2 * x1) / ((y2 - y1) ** 2 + (x2 - x1) ** 2) ** 0.5
        return distance <= threshold

    def is_cursor_near_edge(self, event: tk.Event, threshold: float = 5.0):
        """Check if the cursor is near any edge on the canvas."""
        px, py = event.x, event.y
        for edge, canvas_id in self.edge_shapes.items():
            x1, y1 = edge.node1.get_x_y()
            x2, y2 = edge.node2.get_x_y()
            if self.is_point_near_line(px, py, x1, y1, x2, y2, threshold):
                return edge  # Return the edge if the cursor is near it
        return None  # Return None if no edge is near

    def save_graph_to_file(self, path: str = "graph_data.json") -> None:
        node_positions: dict[str, list[float]] = {
            name: [float(node.get_x_y()[0]), float(node.get_x_y()[1])]
            for name, node in self.graph.nodes.items()
        }

        data: dict[str, Any] = {"nodes": node_positions}

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"Graph saved to {path}")



    def run_loop(self) -> None:
        self.root.mainloop()
        self.save_graph_to_file()


