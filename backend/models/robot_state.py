from dataclasses import dataclass


@dataclass
class RobotFleetState:
    robot_id: str

    x: float
    y: float
    theta: float

    source_timestamp: float
    last_seen: float

    status: str = "ACTIVE"