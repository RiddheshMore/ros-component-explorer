"""
Hardware base class and subclasses for ROS Component Explorer.
Defines the base Hardware class and specific component subclasses.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class Hardware(ABC):
    """Base class for all hardware components."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        self.name = name
        self.description = description
        self.package = package
        self.ros_version = ros_version
        self.inputs: List[str] = []
        self.outputs: List[str] = []
        self.update_rate: Optional[float] = None
    
    @abstractmethod
    def get_component_type(self) -> str:
        """Return the component type."""
        pass
    
    def add_input(self, topic: str):
        """Add an input topic."""
        if topic not in self.inputs:
            self.inputs.append(topic)
    
    def add_output(self, topic: str):
        """Add an output topic."""
        if topic not in self.outputs:
            self.outputs.append(topic)
    
    def to_dict(self) -> Dict:
        """Convert the hardware component to a dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "package": self.package,
            "ros_version": self.ros_version,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "update_rate": self.update_rate,
            "component_type": self.get_component_type()
        }


class Sensor(Hardware):
    """Base class for sensor components."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str, sensor_type: str):
        super().__init__(name, description, package, ros_version)
        self.sensor_type = sensor_type
    
    def get_component_type(self) -> str:
        return "Sensor"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["sensor_type"] = self.sensor_type
        return data


class Camera(Sensor):
    """Camera sensor component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version, "camera")
        self.resolution: Optional[str] = None
        self.fps: Optional[float] = None
    
    def get_component_type(self) -> str:
        return "Camera"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["resolution"] = self.resolution
        data["fps"] = self.fps
        return data


class Lidar(Sensor):
    """Lidar sensor component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version, "lidar")
        self.range_max: Optional[float] = None
        self.angle_resolution: Optional[float] = None
    
    def get_component_type(self) -> str:
        return "Lidar"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["range_max"] = self.range_max
        data["angle_resolution"] = self.angle_resolution
        return data


class Localization(Hardware):
    """Localization component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version)
        self.algorithm: Optional[str] = None
    
    def get_component_type(self) -> str:
        return "Localization"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["algorithm"] = self.algorithm
        return data


class PathPlanner(Hardware):
    """Path planning component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version)
        self.algorithm: Optional[str] = None
    
    def get_component_type(self) -> str:
        return "PathPlanner"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["algorithm"] = self.algorithm
        return data


class Controller(Hardware):
    """Controller component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version)
    
    def get_component_type(self) -> str:
        return "Controller"


class Perception(Hardware):
    """Perception component."""
    
    def __init__(self, name: str, description: str, package: str, ros_version: str):
        super().__init__(name, description, package, ros_version)
        self.algorithm: Optional[str] = None
    
    def get_component_type(self) -> str:
        return "Perception"
    
    def to_dict(self) -> Dict:
        data = super().to_dict()
        data["algorithm"] = self.algorithm
        return data