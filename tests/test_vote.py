import pytest
from pathlib import Path
from agentpool.vote import cast_vote, load_votes, get_entry_votes

def test_cast_upvote(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    votes = load_votes(votes_file)
    assert "sol-abcd1234" in votes
    assert votes["sol-abcd1234"]["score"] == 1

def test_cast_downvote(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "down", voter="anon_0001")
    votes = load_votes(votes_file)
    assert votes["sol-abcd1234"]["score"] == -1

def test_voter_can_only_vote_once(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    votes = load_votes(votes_file)
    assert votes["sol-abcd1234"]["score"] == 1

def test_get_entry_votes(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0002")
    cast_vote(votes_file, "sol-abcd1234", "down", voter="anon_0003")
    score = get_entry_votes(votes_file, "sol-abcd1234")
    assert score == 1

def test_change_vote(tmp_path):
    votes_file = tmp_path / "votes.yaml"
    cast_vote(votes_file, "sol-abcd1234", "up", voter="anon_0001")
    cast_vote(votes_file, "sol-abcd1234", "down", voter="anon_0001")
    votes = load_votes(votes_file)
    assert votes["sol-abcd1234"]["score"] == -1
