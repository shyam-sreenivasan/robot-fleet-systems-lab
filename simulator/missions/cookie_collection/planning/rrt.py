import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    x: float
    y: float


@dataclass
class Node:
    x: float
    y: float
    parent_index: int | None = None


class RRTPlanner:
    """
    Basic 2D RRT planner.

    The planner itself does not know mission semantics.
    It asks the environment whether positions/segments
    are valid for a specific robot.
    """

    def __init__(
        self,
        environment,
        step_size=3.0,
        goal_sample_rate=0.20,
        max_iterations=2000,
        collision_check_resolution=0.5,
        seed=42,
    ):
        self.environment = environment

        self.step_size = step_size
        self.goal_sample_rate = goal_sample_rate
        self.max_iterations = max_iterations

        self.collision_check_resolution = (
            collision_check_resolution
        )

        self.random = random.Random(
            seed
        )

    def plan(
        self,
        robot,
        goal_x,
        goal_y,
    ):
        start = Point(
            robot.state.x,
            robot.state.y,
        )

        goal = Point(
            goal_x,
            goal_y,
        )

        # Direct path available.
        if self._segment_is_free(
            robot,
            start,
            goal,
        ):
            return [
                start,
                goal,
            ]

        nodes = [
            Node(
                x=start.x,
                y=start.y,
                parent_index=None,
            )
        ]

        for _ in range(
            self.max_iterations
        ):
            sample = self._sample(
                goal
            )

            nearest_index = (
                self._nearest_node_index(
                    nodes,
                    sample,
                )
            )

            nearest = nodes[
                nearest_index
            ]

            new_node = self._steer(
                nearest,
                sample,
                nearest_index,
            )

            if not self._segment_is_free(
                robot,
                Point(
                    nearest.x,
                    nearest.y,
                ),
                Point(
                    new_node.x,
                    new_node.y,
                ),
            ):
                continue

            nodes.append(
                new_node
            )

            new_index = (
                len(nodes) - 1
            )

            distance_to_goal = (
                math.hypot(
                    goal.x - new_node.x,
                    goal.y - new_node.y,
                )
            )

            if (
                distance_to_goal
                <= self.step_size
            ):
                if self._segment_is_free(
                    robot,
                    Point(
                        new_node.x,
                        new_node.y,
                    ),
                    goal,
                ):
                    nodes.append(
                        Node(
                            x=goal.x,
                            y=goal.y,
                            parent_index=new_index,
                        )
                    )

                    return self._build_path(
                        nodes
                    )

        return None

    def segment_is_free(
        self,
        robot,
        start_x,
        start_y,
        end_x,
        end_y,
    ):
        """
        Public segment-validity check used by the
        controller when the world changes after planning.
        """

        return self._segment_is_free(
            robot,
            Point(
                start_x,
                start_y,
            ),
            Point(
                end_x,
                end_y,
            ),
        )

    def _sample(
        self,
        goal,
    ):
        if (
            self.random.random()
            < self.goal_sample_rate
        ):
            return goal

        return Point(
            x=self.random.uniform(
                0,
                self.environment.width,
            ),
            y=self.random.uniform(
                0,
                self.environment.height,
            ),
        )

    def _nearest_node_index(
        self,
        nodes,
        point,
    ):
        return min(
            range(len(nodes)),
            key=lambda index: (
                nodes[index].x
                - point.x
            ) ** 2
            + (
                nodes[index].y
                - point.y
            ) ** 2,
        )

    def _steer(
        self,
        source,
        target,
        parent_index,
    ):
        dx = (
            target.x
            - source.x
        )

        dy = (
            target.y
            - source.y
        )

        distance = math.hypot(
            dx,
            dy,
        )

        if distance <= self.step_size:
            return Node(
                x=target.x,
                y=target.y,
                parent_index=parent_index,
            )

        scale = (
            self.step_size
            / distance
        )

        return Node(
            x=(
                source.x
                + dx * scale
            ),
            y=(
                source.y
                + dy * scale
            ),
            parent_index=parent_index,
        )

    def _segment_is_free(
        self,
        robot,
        start,
        end,
    ):
        distance = math.hypot(
            end.x - start.x,
            end.y - start.y,
        )

        samples = max(
            1,
            int(
                distance
                / self.collision_check_resolution
            ),
        )

        for index in range(
            samples + 1
        ):
            t = (
                index
                / samples
            )

            x = (
                start.x
                + t
                * (
                    end.x
                    - start.x
                )
            )

            y = (
                start.y
                + t
                * (
                    end.y
                    - start.y
                )
            )

            if not (
                self.environment.is_position_free_for_robot(
                    robot=robot,
                    x=x,
                    y=y,
                )
            ):
                return False

        return True

    def _build_path(
        self,
        nodes,
    ):
        path = []

        index = (
            len(nodes) - 1
        )

        while index is not None:
            node = nodes[
                index
            ]

            path.append(
                Point(
                    node.x,
                    node.y,
                )
            )

            index = (
                node.parent_index
            )

        path.reverse()

        return path