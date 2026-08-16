import random

from simulator.missions.cookie_collection.cookie import (
    Cookie,
)

from simulator.missions.cookie_collection.edge.event import (
    MissionEvent,
)

class CookieGenerator:
    """
    Generates a deterministic cookie workload from a seed.

    Same seed + same environment => same proposed sequence.
    """

    def __init__(
        self,
        environment,
        event_bus,
        run_id,
        spawn_interval_seconds=5.0,
        seed=42,
        cookie_radius=1.0,
        margin=5.0,
        max_active_cookies=15,
    ):
        self.environment = environment
        self.event_bus = event_bus
        self.run_id = run_id
        self.spawn_interval_seconds = (
            spawn_interval_seconds
        )

        self.cookie_radius = (
            cookie_radius
        )

        self.margin = margin

        self.max_active_cookies = (
            max_active_cookies
        )

        self.random = random.Random(
            seed
        )

        self.elapsed = 0.0
        self.cookie_counter = 0

        self.on_cookie_spawned = None

    def update(
        self,
        dt: float,
    ):
        self.elapsed += dt

        if (
            self.elapsed
            < self.spawn_interval_seconds
        ):
            return

        self.elapsed -= (
            self.spawn_interval_seconds
        )

        if (
            len(
                self.environment.get_cookies()
            )
            >= self.max_active_cookies
        ):
            return

        self._spawn_cookie()

    def _spawn_cookie(self):

        for _ in range(100):

            x = self.random.uniform(
                self.margin,
                self.environment.width
                - self.margin,
            )

            y = self.random.uniform(
                self.margin,
                self.environment.height
                - self.margin,
            )

            if not self.environment.can_spawn_cookie(
                x=x,
                y=y,
                radius=self.cookie_radius,
            ):
                continue

            self.cookie_counter += 1

            cookie = Cookie(
                cookie_id=(
                    f"cookie_{self.cookie_counter:04d}"
                ),
                x=x,
                y=y,
                radius=self.cookie_radius,
            )

            self.environment.add_cookie(
                cookie
            )

            event = MissionEvent.create(
                event_type="COOKIE_SPAWNED",
                mission_id="cookie_collection",
                run_id=self.run_id, 
                metadata={
                    "cookie_id": cookie.cookie_id,
                    "x": cookie.x,
                    "y": cookie.y,
                },
            )

            self.event_bus.publish(
                event
            )

            if (
                self.on_cookie_spawned
                is not None
            ):
                self.on_cookie_spawned(
                    cookie
                )

            return

        print(
            "[SPAWN] Could not find "
            "a valid cookie position."
        )