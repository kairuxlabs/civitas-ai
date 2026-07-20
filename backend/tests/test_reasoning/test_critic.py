from src.reasoning.critic import review


def _decision(confidence=80, flood_risk="low", traffic_disruption="unlikely"):
    return {
        "confidence": confidence,
        "prediction": {"flood_risk": flood_risk, "traffic_disruption": traffic_disruption},
    }


def test_sufficient_evidence_no_notes():
    evidence = [
        {"type": "sensor"}, {"type": "sensor"}, {"type": "sop"},
    ]
    result = review(_decision(), evidence)
    assert result["critic_notes"] == []
    assert result["confidence"] == 80


def test_insufficient_evidence_reduces_confidence():
    evidence = [{"type": "sensor"}]
    result = review(_decision(confidence=80), evidence)
    assert len(result["critic_notes"]) == 1
    assert "insufficient" in result["critic_notes"][0].lower() or "evidence" in result["critic_notes"][0].lower()
    assert result["confidence"] == 65


def test_unsupported_flood_risk_claim():
    evidence = [{"type": "sop"}, {"type": "knowledge"}]
    result = review(_decision(confidence=80, flood_risk="high"), evidence)
    assert any("flood_risk" in n.lower() for n in result["critic_notes"])
    assert result["confidence"] == 65


def test_unsupported_traffic_disruption_claim():
    evidence = [{"type": "sop"}, {"type": "knowledge"}]
    result = review(_decision(confidence=80, traffic_disruption="likely"), evidence)
    assert any("traffic_disruption" in n.lower() for n in result["critic_notes"])


def test_confidence_floored_at_30():
    evidence = []
    result = review(_decision(confidence=40, flood_risk="high", traffic_disruption="likely"), evidence)
    # 3 notes expected: insufficient evidence, unsupported flood_risk, unsupported traffic_disruption
    assert len(result["critic_notes"]) == 3
    assert result["confidence"] == 30
