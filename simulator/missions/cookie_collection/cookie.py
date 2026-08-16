from dataclasses import dataclass
from typing import Optional


@dataclass
class Cookie:
    cookie_id: str

    x: float
    y: float

    radius: float = 1.0

    assigned_robot_id: Optional[str] = None