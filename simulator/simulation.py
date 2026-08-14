import math

import pygame


class Simulation:
    def __init__(
        self,
        arena,
        robots,
        controllers,
        telemetry_publisher=None,
        telemetry_frequency_hz=2.0,
        width_px=800,
        height_px=600,
        background_color=(245, 245, 245),
    ):
        self.arena = arena
        self.robots = robots
        self.controllers = controllers

        self.telemetry_publisher = telemetry_publisher
        self.telemetry_frequency_hz = telemetry_frequency_hz

        self.telemetry_interval_ms = (
            1000.0 / telemetry_frequency_hz
            if telemetry_frequency_hz > 0
            else None
        )

        self.last_telemetry_publish_ms = 0

        self.width_px = width_px
        self.height_px = height_px
        self.background_color = background_color

        pygame.init()

        self.screen = pygame.display.set_mode(
            (
                self.width_px,
                self.height_px,
            )
        )

        pygame.display.set_caption(
            "Robot Fleet Systems Lab - 2D Simulator"
        )

        self.clock = pygame.time.Clock()

    def _publish_telemetry_if_due(self):
        if self.telemetry_publisher is None:
            return

        if self.telemetry_interval_ms is None:
            return

        now_ms = pygame.time.get_ticks()

        elapsed_ms = (
            now_ms
            - self.last_telemetry_publish_ms
        )

        if elapsed_ms < self.telemetry_interval_ms:
            return

        for robot in self.robots:
            self.telemetry_publisher.publish(robot)

        self.last_telemetry_publish_ms = now_ms

    def run(self):
        running = True

        while running:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            for controller in self.controllers:
                controller.step()

            self._publish_telemetry_if_due()

            self.render()

            self.clock.tick(30)

        pygame.quit()

    def render(self):
        self.screen.fill(
            self.background_color
        )

        self._draw_arena()

        # Draw LiDAR underneath the robots.
        for robot in self.robots:
            self._draw_lidar(robot)

        # Draw robot bodies on top of LiDAR.
        for robot in self.robots:
            self._draw_robot(robot)

        self._draw_debug_info()

        pygame.display.flip()

    def _draw_arena(self):
        pygame.draw.rect(
            self.screen,
            (40, 40, 40),
            pygame.Rect(
                0,
                0,
                self.width_px - 1,
                self.height_px - 1,
            ),
            width=3,
        )

    def _draw_lidar(
        self,
        robot,
    ):
        readings = robot.scan()

        if not readings:
            return

        robot_x, robot_y = (
            self._world_to_screen(
                robot.state.x,
                robot.state.y,
            )
        )

        for reading in readings:

            global_angle = (
                robot.state.theta
                + reading.relative_angle
            )

            end_x_world = (
                robot.state.x
                + reading.distance
                * math.cos(global_angle)
            )

            end_y_world = (
                robot.state.y
                + reading.distance
                * math.sin(global_angle)
            )

            end_x, end_y = (
                self._world_to_screen(
                    end_x_world,
                    end_y_world,
                )
            )

            pygame.draw.line(
                self.screen,
                (190, 190, 190),
                (robot_x, robot_y),
                (end_x, end_y),
                width=1,
            )

    def _draw_robot(
        self,
        robot,
    ):
        x_px, y_px = (
            self._world_to_screen(
                robot.state.x,
                robot.state.y,
            )
        )

        robot_radius_px = max(
            3,
            int(
                robot.radius
                / self.arena.width
                * self.width_px
            ),
        )

        pygame.draw.circle(
            self.screen,
            (30, 100, 220),
            (x_px, y_px),
            robot_radius_px,
        )

        heading_length = (
            robot_radius_px + 10
        )

        heading_x = (
            x_px
            + heading_length
            * math.cos(
                robot.state.theta
            )
        )

        # Pygame's y-axis grows downward,
        # while our world y-axis grows upward.
        heading_y = (
            y_px
            - heading_length
            * math.sin(
                robot.state.theta
            )
        )

        pygame.draw.line(
            self.screen,
            (220, 50, 50),
            (x_px, y_px),
            (
                int(heading_x),
                int(heading_y),
            ),
            width=2,
        )

    def _draw_debug_info(self):
        font = pygame.font.Font(
            None,
            26,
        )

        lines = [
            f"Robots: {len(self.robots)}",
            "",
        ]

        for robot in self.robots:

            theta_deg = math.degrees(
                robot.state.theta
            )

            lines.append(
                (
                    f"{robot.robot_id}: "
                    f"({robot.state.x:.1f}, "
                    f"{robot.state.y:.1f}) "
                    f"{theta_deg:.0f}°"
                )
            )

        y_offset = 15

        for line in lines:

            text_surface = font.render(
                line,
                True,
                (20, 20, 20),
            )

            self.screen.blit(
                text_surface,
                (
                    15,
                    y_offset,
                ),
            )

            y_offset += 22

    def _world_to_screen(
        self,
        x,
        y,
    ):
        """
        Convert Arena coordinates into Pygame screen coordinates.

        Arena:
            origin = bottom-left
            +x = right
            +y = up

        Pygame:
            origin = top-left
            +x = right
            +y = down
        """

        x_ratio = (
            x / self.arena.width
        )

        y_ratio = (
            y / self.arena.height
        )

        x_px = int(
            x_ratio
            * self.width_px
        )

        y_px = int(
            self.height_px
            - y_ratio
            * self.height_px
        )

        return x_px, y_px