import pytest

import src.runtime.planner as planner_mod
from src.runtime.planner import AGENT_CATALOG, create_plan, rule_based_plan


def _by_id(specs):
    return {s.id: s for s in specs}


def test_rule_based_plan_for_heavy_rain_goal():
    specs = _by_id(rule_based_plan("Prepare the city for tonight's heavy rain"))

    for expected in ("weather", "knowledge", "citizen", "traffic", "emergency", "forecast", "analytics"):
        assert expected in specs, f"missing task {expected}"
    assert "weather" in specs["traffic"].depends_on
    assert "weather" in specs["forecast"].depends_on
    # analytics runs last: depends on every other task
    assert set(specs["analytics"].depends_on) == set(specs) - {"analytics"}


def test_rule_based_plan_air_pollution_adds_environment():
    specs = _by_id(rule_based_plan("Ô nhiễm không khí nghiêm trọng ở Hà Nội"))
    assert "environment" in specs
    assert "emergency" not in specs


def test_all_planned_agents_are_in_catalog():
    for goal in ("heavy rain flood", "air pollution", "festival event tomorrow", "hello"):
        for spec in rule_based_plan(goal):
            assert spec.agent in AGENT_CATALOG


@pytest.mark.asyncio
async def test_create_plan_falls_back_on_invalid_gemini(monkeypatch):
    monkeypatch.setattr(planner_mod, "call_gemini", lambda *a, **k: "not json at all")
    specs = await create_plan("heavy rain")
    assert {s.id for s in specs} == {s.id for s in rule_based_plan("heavy rain")}


@pytest.mark.asyncio
async def test_create_plan_rejects_unknown_agent(monkeypatch):
    bad = '{"tasks": [{"id": "hack", "agent": "nonexistent", "depends_on": []}]}'
    monkeypatch.setattr(planner_mod, "call_gemini", lambda *a, **k: bad)
    specs = await create_plan("heavy rain")
    # falls back to rule-based
    assert all(s.agent in AGENT_CATALOG for s in specs)
    assert {s.id for s in specs} == {s.id for s in rule_based_plan("heavy rain")}


@pytest.mark.asyncio
async def test_create_plan_accepts_valid_gemini(monkeypatch):
    good = (
        '{"tasks": ['
        '{"id": "weather", "agent": "weather", "depends_on": []},'
        '{"id": "traffic", "agent": "traffic", "depends_on": ["weather"]}'
        "]}"
    )
    monkeypatch.setattr(planner_mod, "call_gemini", lambda *a, **k: good)
    specs = await create_plan("heavy rain")
    assert {s.id for s in specs} == {"weather", "traffic"}


@pytest.mark.asyncio
async def test_create_plan_rejects_cyclic_dag(monkeypatch):
    cyclic = (
        '{"tasks": ['
        '{"id": "a", "agent": "weather", "depends_on": ["b"]},'
        '{"id": "b", "agent": "traffic", "depends_on": ["a"]}'
        "]}"
    )
    monkeypatch.setattr(planner_mod, "call_gemini", lambda *a, **k: cyclic)
    specs = await create_plan("heavy rain")
    assert {s.id for s in specs} == {s.id for s in rule_based_plan("heavy rain")}
