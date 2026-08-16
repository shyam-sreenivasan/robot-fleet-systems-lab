import json
from pathlib import Path
from threading import Lock


class RunEventWriter:

    def __init__(
        self,
        base_directory="data/mission_runs",
    ):
        self.base_directory = Path(
            base_directory
        )

        self.base_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = Lock()

    def append(
        self,
        event,
    ):
        run_directory = (
            self.base_directory
            / event.run_id
        )

        run_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        event_file = (
            run_directory
            / "events.jsonl"
        )

        event_data = (
            event.model_dump()
        )

        with self._lock:
            with event_file.open(
                "a",
                encoding="utf-8",
            ) as file:
                file.write(
                    json.dumps(
                        event_data
                    )
                )

                file.write("\n")