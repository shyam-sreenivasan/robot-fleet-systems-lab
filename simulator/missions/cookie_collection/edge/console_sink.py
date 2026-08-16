import json


class ConsoleEventSink:
    def handle(
        self,
        event,
    ):
        print(
            "[EVENT]",
            json.dumps(
                event.to_dict(),
                indent=2,
            ),
        )