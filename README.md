# Robot Fleet Systems Lab

A modular simulation and experimentation platform for studying robotics fleet infrastructure problems such as telemetry, liveness, network failures, stale state, alerts, reconnect behavior, and fleet observability.

The project is designed as a **systems lab**, not a single finished application.

> Keep the surrounding system stable, introduce one controlled failure or constraint, and observe how the rest of the system behaves.

## V1

Version 1 implements an end-to-end fleet monitoring system:

```text
Simulated Robot Fleet
        |
        | telemetry
        v
Fleet Backend
        |
        +---- Fleet State
        +---- Health Monitoring
        +---- Alerts
        +---- WebSocket Events
        |
        v
Operations Dashboard
```

It also includes an experiment control plane for injecting failures into the running simulator.

Example:

```bash
python -m experiments.simulate_network_failure --robot 4 --duration 20
```

This stops telemetry from `robot_4` for 20 seconds while the robot itself continues moving. The backend detects stale telemetry, marks the robot `UNKNOWN`, raises an alert, and the dashboard freezes the robot at its last known position. When telemetry resumes, the backend catches up and the alert resolves.

## Architecture

```text
                    Experiments
                        |
                        v
               Simulator Control API
                        |
                        v
                  Command Router
                        |
                        v
                Telemetry Control
                        |
                        v

Controller ---> Robot ---> Arena
               |
               +---- LiDAR
               |
               v
        Telemetry Publisher
               |
               | HTTP
               v

                  Fleet Backend
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
       FleetState  HealthMonitor  AlertService
            |           |           |
            +-----------+-----------+
                        |
                        v
                   EventBus
                        |
                        v
              Operations Dashboard
```

## Design Principles

### Agent intent and world state are separate
The Robot proposes actions. The Arena owns the world and determines whether the resulting state is physically valid.

### Perception is separate from physics
The Arena knows world truth. Robots observe the world through sensors such as LiDAR and make decisions from those observations.

### Controllers are external to robots
Controllers decide what the robot should do. The Robot does not know whether commands come from a manual controller, autonomous policy, ROS2, or another control source.

### Telemetry is separate from robot behavior
Robots do not know about HTTP, dashboards, or backend infrastructure. Telemetry is handled through a separate publisher interface.

### Backend state is knowledge, not physical truth
If telemetry stops, the physical robot can continue moving while the backend still contains its last known position.

### Liveness is inferred from freshness
The backend tracks `last_seen`. If telemetry becomes stale beyond the configured timeout:

```text
ACTIVE -> UNKNOWN
```

A `TELEMETRY_LOST` alert is generated.

### Experiments are external to the system being tested
Failure logic is not hard-coded into production components. Experiments send commands through a control plane to the subsystem they want to manipulate.

## Project Structure

```text
.
├── backend/
│   ├── api/
│   ├── models/
│   ├── services/
│   └── storage/
├── simulator/
│   ├── control/
│   ├── controllers/
│   ├── sensors/
│   ├── telemetry/
│   ├── arena.py
│   ├── robot.py
│   └── simulation.py
├── frontend/
│   └── src/
├── experiments/
│   ├── 01_liveness_detection/
│   ├── 02_reconnect_storm/
│   └── simulate_network_failure.py
├── shared/
├── docs/
├── tests/
├── requirements.txt
└── docker-compose.yml
```

### Main Components

**Simulator** — Represents the physical fleet, environment, sensors, controllers, and telemetry generation.

**Backend** — Maintains the latest known fleet state, detects stale robots, manages alerts, and exposes APIs.

**Frontend** — Provides the fleet operations dashboard and backend-known fleet map.

**Experiments** — Inject controlled failures or changes into the running system.

**Shared** — Contains schemas and contracts shared across system boundaries.

## Setup

Clone the repository:

```bash
git clone <repository-url>
cd robot-fleet-systems-lab
```

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
cd ..
```

## Run

### 1. Start the backend

```bash
uvicorn backend.app:app --reload --port 8000
```

Backend: `http://localhost:8000`

### 2. Start the simulator

In another terminal:

```bash
source .venv/bin/activate
python -m simulator.main
```

The simulator also starts the experiment control API at `http://localhost:9000`.

### 3. Start the dashboard

In another terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:5173`.

### 4. Run the V1 experiment

In another terminal from the project root:

```bash
python -m experiments.simulate_network_failure --robot 4 --duration 20
```

Expected behavior:

```text
robot_4 telemetry stops
        |
        v
backend last_seen becomes stale
        |
        v
ACTIVE -> UNKNOWN
        |
        v
TELEMETRY_LOST alert
        |
        v
dashboard freezes robot at last known position
        |
        v
telemetry resumes
        |
        v
UNKNOWN -> ACTIVE
```

The physical robot continues moving throughout the experiment.

## Future Experiments

The same platform can be extended to study:

- reconnect storms
- buffering and replay
- backpressure
- packet loss
- gateway architectures
- sensor degradation
- controller congestion
- backend overload
- data freshness

The goal is to evolve the platform through controlled experiments rather than continuously adding unrelated features.
