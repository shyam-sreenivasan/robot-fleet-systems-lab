from fastapi import FastAPI
from fastapi import HTTPException
import asyncio
from fastapi.middleware.cors import CORSMiddleware

from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from backend.models.telemetry import (
    TelemetryPayload,
)

from backend.services.fleet_state import (
    FleetState,
)

from backend.services.alert_service import (
    AlertService,
)

from backend.services.health_monitor import (
    HealthMonitor,
)
from backend.services.event_bus import EventBus


app = FastAPI(
    title="Robot Fleet Backend"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fleet_state = FleetState()

alert_service = AlertService()

event_bus = EventBus()

health_monitor = HealthMonitor(
    fleet_state=fleet_state,
    alert_service=alert_service,
    event_bus=event_bus,
    timeout_seconds=3.0,
    check_interval_seconds=1.0,
)


@app.on_event("startup")
def startup():

    event_bus.set_event_loop(
        asyncio.get_event_loop()
    )

    health_monitor.start()

@app.websocket("/events")
async def events(
    websocket: WebSocket,
):
    await event_bus.connect(
        websocket
    )

    try:
        while True:
            # We don't currently expect messages from
            # the dashboard. This simply keeps the
            # WebSocket connection alive.
            await websocket.receive_text()

    except WebSocketDisconnect:
        event_bus.disconnect(
            websocket
        )



@app.on_event("shutdown")
def shutdown():
    health_monitor.stop()


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.post("/telemetry")
def receive_telemetry(
    telemetry: TelemetryPayload,
):
    previous_status = (
        fleet_state
        .update_from_telemetry(
            telemetry
        )
    )

    # If this robot was previously UNKNOWN,
    # telemetry has now recovered.
    if previous_status == "UNKNOWN":

        resolved = (
            alert_service
            .resolve_telemetry_lost_alert(
                telemetry.robot_id
            )
        )

        print(
            "[HEALTH] "
            f"{telemetry.robot_id} "
            f"UNKNOWN -> ACTIVE"
        )

        event_bus.publish(
            {
                "type": "ROBOT_STATUS_CHANGED",
                "robot_id": telemetry.robot_id,
                "status": "ACTIVE",
            }
        )

        if resolved:

            event_bus.publish(
                {
                    "type": "ALERT_RESOLVED",
                    "robot_id": telemetry.robot_id,
                    "alert_type": "TELEMETRY_LOST",
                }
            )

    print(
        "[TELEMETRY] "
        f"robot={telemetry.robot_id} "
        f"x={telemetry.x:.2f} "
        f"y={telemetry.y:.2f} "
        f"theta={telemetry.theta:.2f}"
    )

    return {
        "status": "received"
    }


@app.get("/fleet")
def get_fleet():

    robots = (
        fleet_state.get_all()
    )

    return {
        "robots": robots
    }


@app.get("/fleet/{robot_id}")
def get_robot(
    robot_id: str,
):
    robot = (
        fleet_state.get_robot(
            robot_id
        )
    )

    if robot is None:
        raise HTTPException(
            status_code=404,
            detail="Robot not found",
        )

    return robot


@app.get("/alerts")
def get_alerts(
    active_only: bool = False,
):
    alerts = (
        alert_service.get_all(
            active_only=active_only
        )
    )

    return {
        "active_alert_count":
            alert_service.active_count(),

        "alerts": alerts,
    }


@app.get("/summary")
def get_summary():

    fleet_summary = (
        fleet_state.summary()
    )

    return {
        **fleet_summary,

        "active_alert_count":
            alert_service.active_count(),
    }