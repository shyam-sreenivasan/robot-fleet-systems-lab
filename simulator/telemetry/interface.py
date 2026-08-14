from abc import ABC, abstractmethod


class TelemetryPublisher(ABC):

    @abstractmethod
    def publish(self, robot):
        """
        Publish the current telemetry for a robot.
        """
        pass