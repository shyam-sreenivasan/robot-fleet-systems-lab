import math
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class LidarReading:
    relative_angle: float
    distance: float


class Lidar:
    """
    Simple 2D LiDAR.

    Detects:
    - Arena boundaries
    - Other circular robots

    Does not detect the robot it is mounted on.
    """

    def __init__(
        self,
        field_of_view_degrees: float = 150.0,
        num_rays: int = 31,
        max_range: float = 25.0,
    ):
        if field_of_view_degrees <= 0 or field_of_view_degrees > 360:
            raise ValueError(
                "LiDAR field of view must be between 0 and 360 degrees."
            )

        if num_rays < 1:
            raise ValueError(
                "LiDAR must have at least one ray."
            )

        if max_range <= 0:
            raise ValueError(
                "LiDAR maximum range must be greater than zero."
            )

        self.field_of_view = math.radians(
            field_of_view_degrees
        )

        self.num_rays = num_rays
        self.max_range = max_range

    def scan(
        self,
        arena,
        robot,
    ) -> List[LidarReading]:

        readings = []

        for relative_angle in self._ray_angles():

            global_angle = (
                robot.state.theta
                + relative_angle
            )

            wall_distance = self._distance_to_boundary(
                arena=arena,
                x=robot.state.x,
                y=robot.state.y,
                angle=global_angle,
            )

            robot_distance = self._distance_to_other_robots(
                arena=arena,
                scanning_robot=robot,
                angle=global_angle,
            )

            distance = min(
                wall_distance,
                robot_distance,
                self.max_range,
            )

            readings.append(
                LidarReading(
                    relative_angle=relative_angle,
                    distance=distance,
                )
            )

        return readings

    def _ray_angles(self):

        if self.num_rays == 1:
            return [0.0]

        start_angle = (
            -self.field_of_view / 2
        )

        end_angle = (
            self.field_of_view / 2
        )

        step = (
            end_angle - start_angle
        ) / (self.num_rays - 1)

        return [
            start_angle + i * step
            for i in range(self.num_rays)
        ]

    def _distance_to_boundary(
        self,
        arena,
        x,
        y,
        angle,
    ):

        dx = math.cos(angle)
        dy = math.sin(angle)

        distances = []

        epsilon = 1e-9

        # Left / right walls
        if abs(dx) > epsilon:

            # Left wall
            t = (
                0.0 - x
            ) / dx

            if t >= 0:
                intersection_y = (
                    y + t * dy
                )

                if (
                    0.0
                    <= intersection_y
                    <= arena.height
                ):
                    distances.append(t)

            # Right wall
            t = (
                arena.width - x
            ) / dx

            if t >= 0:
                intersection_y = (
                    y + t * dy
                )

                if (
                    0.0
                    <= intersection_y
                    <= arena.height
                ):
                    distances.append(t)

        # Bottom / top walls
        if abs(dy) > epsilon:

            # Bottom wall
            t = (
                0.0 - y
            ) / dy

            if t >= 0:
                intersection_x = (
                    x + t * dx
                )

                if (
                    0.0
                    <= intersection_x
                    <= arena.width
                ):
                    distances.append(t)

            # Top wall
            t = (
                arena.height - y
            ) / dy

            if t >= 0:
                intersection_x = (
                    x + t * dx
                )

                if (
                    0.0
                    <= intersection_x
                    <= arena.width
                ):
                    distances.append(t)

        if not distances:
            return self.max_range

        return min(distances)

    def _distance_to_other_robots(
        self,
        arena,
        scanning_robot,
        angle,
    ):
        """
        Ray-circle intersection against every other robot.

        Returns distance to nearest robot hit.
        """

        origin_x = (
            scanning_robot.state.x
        )

        origin_y = (
            scanning_robot.state.y
        )

        dx = math.cos(angle)
        dy = math.sin(angle)

        closest_distance = (
            self.max_range
        )

        for other_robot in arena.get_robots():

            if (
                other_robot.robot_id
                == scanning_robot.robot_id
            ):
                continue

            center_x = (
                other_robot.state.x
            )

            center_y = (
                other_robot.state.y
            )

            radius = (
                other_robot.radius
            )

            #
            # Vector from circle center
            # to ray origin.
            #
            fx = (
                origin_x
                - center_x
            )

            fy = (
                origin_y
                - center_y
            )

            #
            # Solve:
            #
            # |origin + t * direction - center|² = r²
            #
            # Since direction is normalized:
            #
            # t² + b*t + c = 0
            #

            b = 2 * (
                fx * dx
                + fy * dy
            )

            c = (
                fx * fx
                + fy * fy
                - radius * radius
            )

            discriminant = (
                b * b
                - 4 * c
            )

            if discriminant < 0:
                continue

            sqrt_discriminant = (
                math.sqrt(discriminant)
            )

            t1 = (
                -b
                - sqrt_discriminant
            ) / 2

            t2 = (
                -b
                + sqrt_discriminant
            ) / 2

            valid_distances = [
                t
                for t in (t1, t2)
                if t >= 0
            ]

            if not valid_distances:
                continue

            hit_distance = min(
                valid_distances
            )

            if (
                hit_distance
                < closest_distance
            ):
                closest_distance = (
                    hit_distance
                )

        return closest_distance