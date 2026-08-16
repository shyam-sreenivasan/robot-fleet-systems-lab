# Robot Fleet Systems Lab

A small experimental platform for studying production-style robot fleet systems: telemetry, reliability, fleet coordination, task execution, observability, and capacity planning.

The lab is intentionally modular so robot behavior, fleet infrastructure, failures, and experiment parameters can be changed independently.

────────

### Experiments

##### 1. Telemetry / Liveness Failure

Simulates a robot that keeps moving physically while telemetry to the backend is temporarily suppressed.

This demonstrates:

• backend-known state becoming stale
• ACTIVE → UNKNOWN health transition
• telemetry-loss alerting
• recovery when telemetry resumes
• divergence between physical robot state and platform-known state

Start the backend:

```bash
uvicorn backend.app:app --reload
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Run the simulator:

```bash
python -m simulator.main
```

Inject a telemetry failure:

```bash
python -m experiments.simulate_network_failure \
  --robot 4 \
  --duration 20
```

Fleet dashboard:

```text
http://localhost:5173/
```

────────

##### 2. Robot Fleet Capacity Planning

A cookie-collection mission used to study how fleet size affects:

• throughput
• robot utilization
• queue latency
• task execution latency
• replanning
• planning failures
• contention between robots

Cookies are continuously spawned and assigned to available robots. Each robot uses RRT to plan and execute a path to its assigned task.

Start the backend:

```bash
uvicorn backend.app:app --reload
```

Start the frontend:

```bash
cd frontend
npm run dev
```

Run a 60-second experiment:

```bash
python -m simulator.missions.cookie_collection.main \
  --robot-count 3 \
  --duration 60
```

Supported fleet sizes:

```text
3
7
10
```

Example:

```bash
python -m simulator.missions.cookie_collection.main \
  --robot-count 7 \
  --duration 60
```

Cookie mission dashboard:

```text
http://localhost:5173/cookiemission
```

Mission events are saved under:

```text
data/mission_runs/<run_id>/events.jsonl
```

Analyze a completed run:

```bash
python experiments/analyze_cookie_run.py \
  data/mission_runs/<run_id>/events.jsonl
```

The analysis includes:

• cookies collected/min
• cookies collected/robot/min
• average open tasks
• queue and execution latency
• p50 / p95 mission latency
• replans
• planning failures
• idle time per robot

────────

Architecture

```text
Robot / Mission
      ↓
Edge Event Bus
      ↓
Backend
      ├── Fleet state + health monitoring
      ├── Mission event storage
      └── Metric aggregation
              ↓
           Dashboard
```

The simulator owns physical state. The backend observes the fleet through telemetry and mission events.

────────

Setup

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```