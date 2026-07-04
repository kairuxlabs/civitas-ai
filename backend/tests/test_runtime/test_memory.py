from src.runtime.memory import DecisionMemory, KnowledgeMemory


def test_knowledge_memory_finds_flood_sop():
    memory = KnowledgeMemory()
    results = memory.search("heavy rain flood in Hanoi", k=2)
    assert results
    assert any("flood" in r["title"].lower() for r in results)
    assert {"id", "title", "content", "score"} <= set(results[0])


def test_knowledge_memory_empty_for_unrelated_query():
    memory = KnowledgeMemory()
    assert memory.search("quantum computing budget", k=3) == []


def test_decision_memory_stores_and_returns_chain():
    memory = DecisionMemory()
    memory.store_chain(
        incident={"type": "heavy_rain", "district_id": 1},
        decision={"summary": "deploy pumps", "confidence": 90},
        workflow={"steps": ["notify", "create_incident"]},
        outcome="approved",
    )
    chains = memory.recent(5)
    assert len(chains) == 1
    chain = chains[0]
    assert chain["incident"]["type"] == "heavy_rain"
    assert chain["outcome"] == "approved"
    assert chain["ts"]


def test_decision_memory_recent_limit_and_order():
    memory = DecisionMemory()
    for i in range(5):
        memory.store_chain({"i": i}, {}, {}, "done")
    recent = memory.recent(3)
    assert len(recent) == 3
    assert recent[0]["incident"]["i"] == 4  # newest first
