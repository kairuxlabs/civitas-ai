import json

from src.runtime.state import (
    RunState,
    RunStatus,
    RunStore,
    TaskSpec,
    TaskStatus,
)


def _make_run() -> RunState:
    run = RunState(goal="Prepare for heavy rain", district_id=1)
    run.add_tasks([
        TaskSpec(id="weather", agent="weather"),
        TaskSpec(id="traffic", agent="traffic", depends_on=["weather"]),
        TaskSpec(id="knowledge", agent="knowledge"),
    ])
    return run


def test_ready_tasks_respects_dependencies():
    run = _make_run()
    ready_ids = {t.spec.id for t in run.ready_tasks()}
    assert ready_ids == {"weather", "knowledge"}

    run.tasks["weather"].status = TaskStatus.DONE
    ready_ids = {t.spec.id for t in run.ready_tasks()}
    assert "traffic" in ready_ids


def test_failed_dependency_blocks_dependent_and_run_settles():
    run = _make_run()
    run.tasks["weather"].status = TaskStatus.FAILED
    run.tasks["knowledge"].status = TaskStatus.DONE

    assert all(t.spec.id != "traffic" for t in run.ready_tasks())
    assert run.all_settled() is True


def test_all_settled_false_while_pending_runnable():
    run = _make_run()
    assert run.all_settled() is False


def test_to_dict_is_json_serializable():
    run = _make_run()
    run.log("Plan created", actor="planner")
    data = run.to_dict()
    json.dumps(data)  # must not raise
    assert data["goal"] == "Prepare for heavy rain"
    assert data["status"] == RunStatus.PLANNING.value
    assert len(data["tasks"]) == 3
    assert data["timeline"][0]["message"] == "Plan created"


def test_run_store_add_get_list():
    store = RunStore()
    run = _make_run()
    store.add(run)
    assert store.get(run.run_id) is run
    assert store.get("missing") is None
    assert store.list_recent()[0] is run
