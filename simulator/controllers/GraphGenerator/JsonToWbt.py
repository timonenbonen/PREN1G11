import json
import math

def calculate_angle_and_distance(x1, y1, x2, y2):
    """Calculate the angle and distance between two points."""
    dx = x2 - x1
    dy = y2 - y1
    angle = math.atan2(dy, dx)  # Angle in radians
    distance = math.sqrt(dx**2 + dy**2)
    return angle, distance

def generate_wbt(json_file, output_file):
    """Generate a .wbt file from a JSON file."""
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Base WBT structure
    base_wbt = """#VRML_SIM R2023b utf8

EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2023b/projects/objects/backgrounds/protos/TexturedBackground.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2023b/projects/objects/backgrounds/protos/TexturedBackgroundLight.proto"
EXTERNPROTO "https://raw.githubusercontent.com/cyberbotics/webots/R2023b/projects/objects/floors/protos/RectangleArena.proto"

WorldInfo {
}
Viewpoint {
  orientation -0.2560803139938966 -0.10364928024260135 0.9610825664270359 3.883582953441661
  position -1.4462580638620823 -1.3199776289403695 2.0639717998590306
}
TexturedBackground {
}
TexturedBackgroundLight {
}
RectangleArena {
  floorSize 10 10
  floorTileSize 0.4 0.4
  floorAppearance Appearance {
    material Material {
      diffuseColor 1 1 1
      shininess 0.8
      specularColor 0.1 0.1 0.1
      emissiveColor 0 0 0
    }
    texture ImageTexture {
      url [
        "../../tile.png"
      ]
    }
  }
  wallHeight 1
  wallAppearance PBRAppearance {
    baseColor 0.5 0.5 0.5
    roughness 1
    metalness 0
  }
}
PointLight {
  location 0 5 0
  color 1 1 1
  intensity 2
  attenuation 0 0 0.1
  on TRUE
}
"""

    poses = []

    # Add Pose elements for nodes
    for node, position in data["nodes"].items():
        x, y = position
        pose = f"""Pose {{
  translation {x} {y} 0
  children [
    Shape {{
      geometry Cylinder {{
        height 0.01
        radius 0.08
      }}
    }}
  ]
}}"""
        poses.append(pose)

    # Add Pose elements for edges
    for edge in data["edges"]:
        node1, node2 = edge["node1"], edge["node2"]
        x1, y1 = data["nodes"][node1]
        x2, y2 = data["nodes"][node2]
        angle, distance = calculate_angle_and_distance(x1, y1, x2, y2)
        pose = f"""Pose {{
  translation {(x1 + x2) / 2} {(y1 + y2) / 2} 0
  rotation 0 0 1 {angle}
  children [
    Shape {{
      geometry Box {{
        size {distance} 0.02 0.01
      }}
    }}
  ]
}}"""
        poses.append(pose)

    # Combine all parts
    wbt_content = base_wbt + "\n".join(poses)

    # Write to the output file
    with open(output_file, 'w') as file:
        file.write(wbt_content)
