import pytest
from pathlib import Path
from agentpool.sync import get_data_dir, load_all_entries

def test_get_data_dir():
    d = get_data_dir()
    assert d == Path.home() / ".agentpool"

def test_load_all_entries_empty(tmp_path):
    entries = load_all_entries(tmp_path)
    assert entries == []

def test_load_all_entries_with_files(tmp_path):
    solutions_dir = tmp_path / "entries" / "solutions"
    solutions_dir.mkdir(parents=True)
    (solutions_dir / "test.yaml").write_text("""id: sol-abcd1234
type: solution
title: Test Solution
problem: A problem
solution: The fix
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
""")
    tips_dir = tmp_path / "entries" / "tips"
    tips_dir.mkdir(parents=True)
    (tips_dir / "test-tip.yaml").write_text("""id: tip-efgh5678
type: tip
title: Test Tip
content: A useful tip
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
""")
    entries = load_all_entries(tmp_path)
    assert len(entries) == 2

def test_load_all_entries_skips_malformed(tmp_path):
    solutions_dir = tmp_path / "entries" / "solutions"
    solutions_dir.mkdir(parents=True)
    (solutions_dir / "good.yaml").write_text("""id: sol-abcd1234
type: solution
title: Good
problem: A problem
solution: The fix
tags: [test]
contributor: anon_0000
created: '2026-03-13'
votes: 0
""")
    (solutions_dir / "bad.yaml").write_text("this is not valid yaml: [")
    entries = load_all_entries(tmp_path)
    assert len(entries) == 1
