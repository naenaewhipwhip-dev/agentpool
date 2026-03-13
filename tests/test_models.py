import pytest
from agentpool.models import Solution, Tip, generate_id, load_entry, validate_entry


def test_generate_solution_id():
    entry_id = generate_id("solution")
    assert entry_id.startswith("sol-")
    assert len(entry_id) == 12


def test_generate_tip_id():
    entry_id = generate_id("tip")
    assert entry_id.startswith("tip-")
    assert len(entry_id) == 12


def test_solution_model_valid():
    sol = Solution(
        title="Test solution",
        problem="Something breaks",
        solution="Fix it this way",
        tags=["test"],
    )
    assert sol.type == "solution"
    assert sol.id.startswith("sol-")
    assert sol.votes == 0


def test_tip_model_valid():
    tip = Tip(
        title="Test tip",
        content="Do this thing",
        tags=["test"],
    )
    assert tip.type == "tip"
    assert tip.id.startswith("tip-")


def test_solution_to_yaml():
    sol = Solution(
        title="Test",
        problem="Problem",
        solution="Solution",
        tags=["a", "b"],
    )
    yaml_str = sol.to_yaml()
    assert "type: solution" in yaml_str
    assert "title: Test" in yaml_str
    assert "problem:" in yaml_str


def test_load_entry_solution(tmp_path):
    yaml_content = """id: sol-abcd1234
type: solution
title: Test
problem: Something breaks
solution: Fix it
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
"""
    f = tmp_path / "test.yaml"
    f.write_text(yaml_content)
    entry = load_entry(f)
    assert isinstance(entry, Solution)
    assert entry.title == "Test"


def test_validate_entry_rejects_missing_fields():
    with pytest.raises(ValueError):
        Solution(title="", problem="", solution="", tags=[])
