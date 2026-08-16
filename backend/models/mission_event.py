from typing import Any

from pydantic import BaseModel


class MissionEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: float
    mission_id: str
    run_id: str

    robot_id: str | None = None
    state: dict[str, Any] | None = None
    metadata: dict[str, Any] = {}