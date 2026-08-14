from dataclasses import dataclass
from typing import Optional


@dataclass
class Alert:
    alert_id: str

    robot_id: str
    alert_type: str

    status: str

    started_at: float
    last_seen_at: float

    resolved_at: Optional[float] = None