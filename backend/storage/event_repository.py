from threading import Lock

from backend.models.mission_event import MissionEvent


class EventRepository:
    """
    In-memory event store.

    Good enough for the current experiment framework.
    """

    def __init__(self):
        self._events: list[MissionEvent] = []
        self._lock = Lock()

    def add(
        self,
        event: MissionEvent,
    ):
        with self._lock:
            self._events.append(
                event
            )

    def clear(
        self,
    ):
        with self._lock:
            self._events.clear()

    def get_all(
        self,
        event_type: str | None = None,
        robot_id: str | None = None,
        mission_id: str | None = None,
    ) -> list[MissionEvent]:

        with self._lock:
            events = list(
                self._events
            )

        if event_type is not None:
            events = [
                event
                for event in events
                if event.event_type == event_type
            ]

        if robot_id is not None:
            events = [
                event
                for event in events
                if event.robot_id == robot_id
            ]

        if mission_id is not None:
            events = [
                event
                for event in events
                if event.mission_id == mission_id
            ]

        return events