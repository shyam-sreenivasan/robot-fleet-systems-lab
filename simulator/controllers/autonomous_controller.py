import math
import random

from simulator.controllers.controller import Controller


class AutonomousController(Controller):

    def __init__(
        self,
        robot,
        obstacle_threshold=4.0,
        slow_speed_scale=0.3,
    ):
        self.robot = robot
        self.obstacle_threshold = obstacle_threshold
        self.slow_speed_scale = slow_speed_scale

        # Avoidance maneuver state
        self.remaining_turn = 0.0
        self.turn_direction = None

    def step(self):
        """
        Execute one controller step.

        Priority:

        1. Finish an active avoidance maneuver.
        2. Check whether a new avoidance maneuver is required.
        3. Otherwise execute normal stochastic motion.
        """

        # --------------------------------------------------
        # 1. Continue an existing avoidance maneuver
        # --------------------------------------------------

        if self.remaining_turn > 0:
            self._continue_turn()
            return

        readings = self.robot.scan()

        # --------------------------------------------------
        # 2. Determine whether avoidance is necessary
        # --------------------------------------------------

        blocked_count = self._count_blocked_rays(readings)

        if blocked_count > 0:
            self._start_avoidance(
                readings,
                blocked_count,
            )

            self._continue_turn()
            return

        # --------------------------------------------------
        # 3. Normal movement policy
        # --------------------------------------------------

        self._normal_motion()

    def _normal_motion(self):
        """
        Normal wandering behavior.

        90%   forward
        2.5%  turn left
        2.5%  turn right
        5%    slow forward
        """

        action = random.random()

        if action < 0.90:
            self.robot.move_forward()

        elif action < 0.925:
            self.robot.turn_left()

        elif action < 0.95:
            self.robot.turn_right()

        else:
            self.robot.move_forward(
                speed_scale=self.slow_speed_scale
            )

    def _count_blocked_rays(self, readings):
        """
        Count rays whose measured distance is inside
        the obstacle avoidance threshold.
        """

        return sum(
            1
            for reading in readings
            if reading.distance < self.obstacle_threshold
        )

    def _start_avoidance(
        self,
        readings,
        blocked_count,
    ):
        """
        Start a new avoidance maneuver.

        More blocked rays => larger turn.

        0% blocked   ->   0 degrees
        50% blocked ->  90 degrees
        100% blocked -> 180 degrees
        """

        blocked_ratio = (
            blocked_count / len(readings)
        )

        self.remaining_turn = (
            math.pi * blocked_ratio
        )

        self.turn_direction = (
            self._choose_turn_direction(readings)
        )

    def _choose_turn_direction(self, readings):
        """
        Turn toward the side with more free space.
        """

        center = len(readings) // 2

        right_readings = readings[:center]
        left_readings = readings[center + 1:]

        right_clearance = sum(
            reading.distance
            for reading in right_readings
        ) / len(right_readings)

        left_clearance = sum(
            reading.distance
            for reading in left_readings
        ) / len(left_readings)

        if left_clearance >= right_clearance:
            return "left"

        return "right"

    def _continue_turn(self):
        """
        Execute the avoidance rotation gradually.

        Robot.turn_left/right() already rotates by
        robot.angular_step each simulation frame.
        """

        turn_step = min(
            self.robot.angular_step,
            self.remaining_turn,
        )

        if self.turn_direction == "left":
            self.robot.turn_left()

        else:
            self.robot.turn_right()

        self.remaining_turn -= turn_step

        if self.remaining_turn <= 0:
            self.remaining_turn = 0
            self.turn_direction = None