import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class MissionEvent:
    event_id: str
    event_type: str
    timestamp: float
    mission_id: str
    run_id: str

    robot_id: str | None = None

    state: dict[str, Any] | None = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def create(
        cls,
        event_type: str,
        mission_id: str,
        run_id: str,
        robot_id: str | None = None,
        state: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=time.time(),
            mission_id=mission_id,
            run_id=run_id,
            robot_id=robot_id,
            state=state,
            metadata=metadata or {},
        )

    def to_dict(self):
        return asdict(self)