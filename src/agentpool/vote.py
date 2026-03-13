from __future__ import annotations
from pathlib import Path
import yaml

def load_votes(votes_file: Path) -> dict:
    if not votes_file.exists():
        return {}
    return yaml.safe_load(votes_file.read_text()) or {}

def save_votes(votes_file: Path, votes: dict) -> None:
    votes_file.parent.mkdir(parents=True, exist_ok=True)
    votes_file.write_text(yaml.dump(votes, default_flow_style=False, sort_keys=False))

def cast_vote(votes_file: Path, entry_id: str, direction: str, voter: str = "anonymous") -> int:
    votes = load_votes(votes_file)
    if entry_id not in votes:
        votes[entry_id] = {"score": 0, "voters": {}}

    # One vote per voter per entry
    existing = votes[entry_id]["voters"].get(voter)
    if existing == direction:
        # Already voted this way
        return votes[entry_id]["score"]

    # Remove old vote if changing
    if existing:
        votes[entry_id]["score"] += 1 if existing == "down" else -1

    # Apply new vote
    votes[entry_id]["voters"][voter] = direction
    votes[entry_id]["score"] += 1 if direction == "up" else -1

    save_votes(votes_file, votes)
    return votes[entry_id]["score"]

def get_entry_votes(votes_file: Path, entry_id: str) -> int:
    votes = load_votes(votes_file)
    return votes.get(entry_id, {}).get("score", 0)
