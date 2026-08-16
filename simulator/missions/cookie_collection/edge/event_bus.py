class EdgeEventBus:
    """
    Local mission event bus.

    Mission components publish events here.
    Sinks decide what to do with them.
    """

    def __init__(self):
        self._sinks = []

    def register_sink(
        self,
        sink,
    ):
        self._sinks.append(
            sink
        )

    def publish(
        self,
        event,
    ):
        for sink in self._sinks:
            sink.handle(
                event
            )