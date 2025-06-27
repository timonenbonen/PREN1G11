from roboter_final.Graph.Shape import Shape
from roboter_final.Graph.Cylinder import Cylinder
import math


class Box(Shape):
    def __init__(self, name: str, node1: Cylinder, node2: Cylinder, base_color: tuple[float, float, float] = (1, 1, 1),
                 metalness: float = 0, has_obstacle: bool = False, is_removed: bool = False,
                 obstacle_delay_in_sec: float = 15.0):
        self.name: str = name
        self.node1: Cylinder = node1
        self.node2: Cylinder = node2
        self.base_color: tuple[float, float, float] = base_color
        self.metalness: float = metalness
        self.has_obstacle: bool = has_obstacle
        self.is_removed: bool = is_removed
        self.obstacle_delay_in_sec: float = obstacle_delay_in_sec

    def get_length_and_angle(self) -> tuple[float, float]:
        x1, y1 = self.node1.get_x_y()
        x2, y2 = self.node2.get_x_y()
        dx: float = x2 - x1
        dy: float = y2 - y1
        return (dx ** 2 + dy ** 2) ** 0.5, math.atan2(dy, dx)

    def get_position(self) -> tuple[float, float, float]:
        position_node_1: tuple[float, float] = self.node1.get_x_y()
        position_node_2: tuple[float, float] = self.node2.get_x_y()
        return (position_node_1[0] + position_node_2[0]) / 2, (position_node_1[1] + position_node_2[1]) / 2, 0
    def set_has_obstacle(self, has_obstacle: bool):
        self.has_obstacle = bool(has_obstacle)
    def change_has_obstacle(self):
        self.has_obstacle = not self.has_obstacle

    def change_is_removed(self):
        self.is_removed = not self.is_removed

    def set_is_removed(self, is_removed: bool):
        self.is_removed = bool(is_removed)

    def get_has_obstacle(self) -> bool:
        return self.has_obstacle

    @staticmethod
    def calculate_traversal_time_distance_in_meters(distance: float, max_speed: float, acceleration: float,
                                                    braking_speed: float) -> float:
        accel_distance: float = max_speed ** 2 / (2 * acceleration)
        brake_distance: float = max_speed ** 2 / (2 * braking_speed)
        if distance >= accel_distance + brake_distance:
            # Time to reach max speed
            accel_time = max_speed / acceleration
            brake_time = max_speed / braking_speed

            # Constant speed distance and time
            constant_speed_distance = distance - (accel_distance + brake_distance)
            constant_speed_time = constant_speed_distance / max_speed

            # Total time
            total_time = accel_time + constant_speed_time + brake_time
        else:
            # Robot doesn't reach max speed
            peak_speed = math.sqrt(2 * acceleration * braking_speed * distance / (acceleration + braking_speed))
            accel_time = peak_speed / acceleration
            brake_time = peak_speed / braking_speed

            # Total time
            total_time = accel_time + brake_time

        return total_time

    def calculate_traversal_time_edge(self, max_speed: float, acceleration: float, braking_speed: float, align_time: float) -> float:
        edge_length: float = self.get_length_and_angle()[0]

        if self.has_obstacle:
            # Obstacle specifics
            obstacle_width = 0.03  # Obstacle length is 3 cm
            distance_to_obstacle: float = (edge_length - obstacle_width) / 2
            total_time = (
                    align_time
                    + self.calculate_traversal_time_distance_in_meters(distance=distance_to_obstacle,
                                                                        max_speed=max_speed,
                                                                        acceleration=acceleration,
                                                                        braking_speed=braking_speed)
                    * 2
                    + self.obstacle_delay_in_sec
            )

        else:
            total_time = align_time + self.calculate_traversal_time_distance_in_meters(

                distance=edge_length,
                max_speed=max_speed,
                acceleration=acceleration,
                braking_speed=braking_speed
            )

        return total_time

    def to_vrml(self) -> str:
        position: tuple[float, float, float] = self.get_position()
        length, angle = self.get_length_and_angle()
        if self.is_removed:
            return ""
        else:
            return f"""
            DEF {self.name} Pose {{
              translation {position[0]} {position[1]} {position[2]}
              rotation 0 0 1 {angle}
              children [
                Shape {{
                  appearance PBRAppearance {{
                    baseColor {self.base_color[0]} {self.base_color[1]} {self.base_color[2]}
                    metalness {self.metalness}
                  }}
                  geometry Box {{
                    size {length} 0.02 0.01
                  }}
                }}
              ]
            }}
            
            """

    def obstacle_to_vrml(self):
        if not self.has_obstacle:
            return ""

        else:
            position: tuple[float, float, float] = self.get_position()
            angle: float = self.get_length_and_angle()[1]+math.pi/2
            scale: float = 1
            return f"""
            DEF {self.name}_obstacle Transform {{
              translation {position[0]} {position[1]} {position[2]}
              rotation 0 0 0 {angle}
              scale {scale} {scale} {scale}
              children [
                Shape {{
                  appearance PBRAppearance {{
                    baseColor 0.7 0.7 0.7
                    roughness 0.5
                    metalness 0.1
                  }}
                  geometry Mesh {{
                    url ["../../hindernis.obj"]
                  }}
                }}
              ]
            }}
                """

    def set_base_color(self, base_color: tuple[float, float, float]):
        self.base_color = base_color
