from pydantic import BaseModel


class TelemetryPayload(BaseModel):
    robot_id: str
    timestamp: float
    x: float
    y: float
    theta: float