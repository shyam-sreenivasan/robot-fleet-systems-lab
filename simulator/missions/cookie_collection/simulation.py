import pygame

from simulator.simulation import Simulation
import time


class CookieMissionSimulation(
    Simulation
):

    def __init__(
        self,
        cookie_generator,
        task_controller,
        live_state_publisher=None,
        live_state_frequency_hz=10.0,
        headless=False,
        duration_seconds=None,
        *args,
        **kwargs,
    ):
        super().__init__(
            *args,
            **kwargs,
        )

        self.cookie_generator = (
            cookie_generator
        )

        self.task_controller = (
            task_controller
        )

        self.live_state_publisher = (
            live_state_publisher
        )

        self.headless = headless

        self.duration_seconds = (
            duration_seconds
        )

        # Fixed simulation timestep.
        self.dt = 1.0 / 30.0

        self.simulation_elapsed = 0.0

        # ----------------------------------------------------------
        # Live operational state
        # ----------------------------------------------------------

        self.live_state_frequency_hz = (
            live_state_frequency_hz
        )

        self.live_state_interval = (
            1.0
            / live_state_frequency_hz
        )

        self.live_state_elapsed = 0.0

    def run(self):

        running = True
        started_at = time.monotonic()
        print(
            "[SIMULATION START] "
            f"duration_seconds={self.duration_seconds} "
            f"headless={self.headless}"
        )

        while running:

            # ------------------------------------------------------
            # Window events
            # ------------------------------------------------------

            if not self.headless:

                for event in pygame.event.get():

                    if event.type == pygame.QUIT:
                        running = False

            # ------------------------------------------------------
            # Stop after configured experiment duration
            # ------------------------------------------------------

            if self.duration_seconds is not None:
                wall_elapsed = (
                    time.monotonic()
                    - started_at
                )

                if wall_elapsed >= self.duration_seconds:
                    running = False
                    continue

            # ------------------------------------------------------
            # Mission workload
            # ------------------------------------------------------

            self.cookie_generator.update(
                self.dt
            )

            # ------------------------------------------------------
            # Robot control
            # ------------------------------------------------------

            for controller in self.controllers:
                controller.step()

            # ------------------------------------------------------
            # Physical cookie collection
            # ------------------------------------------------------

            for robot in self.robots:

                cookie = (
                    self.arena.collect_if_reached(
                        robot
                    )
                )

                if cookie is not None:

                    self.task_controller.handle_collection(
                        robot=robot,
                        cookie=cookie,
                    )

            # ------------------------------------------------------
            # Live mission state
            #
            # Skip this entirely during headless experiment runs.
            # The durable mission events are still published.
            # ------------------------------------------------------

            if (
                not self.headless
                and
                self.live_state_publisher
                is not None
            ):

                self.live_state_elapsed += (
                    self.dt
                )

                if (
                    self.live_state_elapsed
                    >= self.live_state_interval
                ):
                    self.live_state_elapsed -= (
                        self.live_state_interval
                    )

                    self.live_state_publisher.publish(
                        robots=self.robots,
                        environment=self.arena,
                    )

            # ------------------------------------------------------
            # Local visualization
            # ------------------------------------------------------

            if not self.headless:
                self.render()

            # ------------------------------------------------------
            # Advance simulation time
            # ------------------------------------------------------

            self.simulation_elapsed += (
                self.dt
            )

            # Keep experiment at real-time 30 Hz for now.
            self.clock.tick(30)

        print(
            "[MISSION COMPLETE] "
            f"simulation_time="
            f"{self.simulation_elapsed:.1f}s"
        )

        if not self.headless:
            pygame.quit()

    def render(self):

        self.screen.fill(
            self.background_color
        )

        self._draw_arena()

        self._draw_cookies()

        for robot in self.robots:
            self._draw_lidar(
                robot
            )

        for robot in self.robots:
            self._draw_robot(
                robot
            )

        self._draw_debug_info()

        pygame.display.flip()

    def _draw_cookies(self):

        for cookie in (
            self.arena.get_cookies()
        ):

            x_px, y_px = (
                self._world_to_screen(
                    cookie.x,
                    cookie.y,
                )
            )

            radius_px = max(
                4,
                int(
                    cookie.radius
                    / self.arena.width
                    * self.width_px
                ),
            )

            pygame.draw.circle(
                self.screen,
                (220, 160, 40),
                (
                    x_px,
                    y_px,
                ),
                radius_px,
            )

            if (
                cookie.assigned_robot_id
                is not None
            ):
                pygame.draw.circle(
                    self.screen,
                    (80, 80, 80),
                    (
                        x_px,
                        y_px,
                    ),
                    radius_px + 2,
                    width=1,
                )