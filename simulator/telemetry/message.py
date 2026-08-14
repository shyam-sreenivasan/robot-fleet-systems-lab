from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TelemetryMessage:
    robot_id: str
    timestamp: float
    x: float
    y: float
    theta: float

    def to_dict(self):
        return asdict(self)