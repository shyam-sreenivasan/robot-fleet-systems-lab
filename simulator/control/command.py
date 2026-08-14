from pydantic import BaseModel
from typing import Optional


class ExperimentCommand(BaseModel):
    target: str
    action: str

    robot_id: Optional[str] = None
    duration_seconds: Optional[float] = None