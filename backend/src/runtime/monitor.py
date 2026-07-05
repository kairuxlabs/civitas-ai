# backend/src/runtime/monitor.py
"""Runtime monitor (spec_v2 §16 Agent Monitor): per-agent health derived
from the operational memory (RunStore)."""
from src.runtime.state import TaskStatus, run_store


def snapshot() -> dict:
    agents: dict[str, dict] = {}
    for run in run_store.list_recent(limit=50):
        for task in run.tasks.values():
            stats = agents.setdefault(task.spec.agent, {
                "runs": 0, "failures": 0, "latencies": [], "last_status": "idle",
            })
            if task.status in (TaskStatus.DONE, TaskStatus.FAILED):
                stats["runs"] += 1
                if task.status == TaskStatus.FAILED:
                    stats["failures"] += 1
                if task.latency_ms is not None:
                    stats["latencies"].append(task.latency_ms)
            stats["last_status"] = task.status.value

    return {
        "agents": {
            name: {
                "runs": s["runs"],
                "failures": s["failures"],
                "avg_latency_ms": round(sum(s["latencies"]) / len(s["latencies"]), 1) if s["latencies"] else None,
                "last_status": s["last_status"],
            }
            for name, s in agents.items()
        },
        "active_runs": sum(
            1 for r in run_store.list_recent(limit=50)
            if r.status.value in ("planning", "running", "reflecting", "deciding")
        ),
        "total_runs": len(run_store.list_recent(limit=50)),
    }
