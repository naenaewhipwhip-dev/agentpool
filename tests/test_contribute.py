import pytest
from pathlib import Path
from agentpool.contribute import create_entry_file, slugify


def test_slugify():
    assert slugify("Rate Limit Backoff!") == "rate-limit-backoff"
    assert slugify("Qdrant batch_size tip") == "qdrant-batch-size-tip"


def test_create_solution_file(tmp_path):
    path = create_entry_file(
        output_dir=tmp_path,
        entry_type="solution",
        title="Test Solution",
        problem="Something breaks",
        solution="Fix it this way",
        tags=["test", "demo"],
    )
    assert path.exists()
    assert path.suffix == ".yaml"
    assert "solutions" in str(path)
    content = path.read_text()
    assert "type: solution" in content
    assert "Test Solution" in content


def test_create_tip_file(tmp_path):
    path = create_entry_file(
        output_dir=tmp_path,
        entry_type="tip",
        title="Quick Tip",
        content="Do this thing",
        tags=["test"],
    )
    assert path.exists()
    assert "tips" in str(path)
    content = path.read_text()
    assert "type: tip" in content


def test_slugify_special_chars():
    assert slugify("Hello, World! @#$") == "hello-world"
    assert slugify("  spaces  everywhere  ") == "spaces-everywhere"
