from roboter_final.Graph.Shape import Shape


class Cylinder(Shape):

    def __init__(self, name: str, position_x_y: tuple[float, float], position_z: float = 0,
                 base_color: tuple[float, float, float] = (1, 1, 1),
                 metalness: float = 0, is_blocked: bool = False):
        self.name: str = name
        self.position: tuple[float, float, float] = (position_x_y[0], position_x_y[1], position_z)
        self.base_color: tuple[float, float, float] = base_color
        self.metalness: float = metalness
        self.is_blocked: bool = is_blocked

    def get_name(self) -> str:
        return self.name

    def get_x_y(self) -> tuple[float, float]:
        return self.position[0], self.position[1]

    def set_x_y(self, x: float, y: float):
        self.position = (x, y, self.position[2])

    def change_is_blocked(self):
        self.is_blocked = not self.is_blocked

    def mirror_y_axis(self, coordination_system_size: float) -> None:
        new_coordinates: tuple[float, float, float] = (
        self.position[0], coordination_system_size - self.position[1], self.position[2])
        self.position = new_coordinates

    def to_vrml(self):
        return f"""
        DEF {self.name} Pose {{
          translation {self.position[0]} {self.position[1]} {self.position[2]}
          children [
            Shape {{
              appearance PBRAppearance {{
                baseColor {self.base_color[0]} {self.base_color[1]} {self.base_color[2]}
                metalness {self.metalness}
              }}
              geometry Cylinder {{
                height 0.01
                radius 0.08
              }}
            }}
          ]
        }}
        
        """

    def blocked_to_vrml(self):
        if not self.is_blocked:
            return ""

        else:
            return f"""
        TrafficCone {{
          translation {self.position[0]} {self.position[1]} 0
          scale 0.3
        }}
            """

    def set_base_color(self, base_color: tuple[float, float, float]):
        self.base_color = base_color
