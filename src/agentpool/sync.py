from pathlib import Path
import subprocess
from agentpool.models import load_entry, Solution, Tip

REPO_URL = "https://github.com/naenaewhipwhip-dev/agentpool.git"

def get_data_dir() -> Path:
    return Path.home() / ".agentpool"

def sync_repo() -> Path:
    data_dir = get_data_dir()
    repo_dir = data_dir / "repo"
    if (repo_dir / ".git").exists():
        subprocess.run(["git", "-C", str(repo_dir), "pull", "--ff-only"],
                       check=True, capture_output=True)
    else:
        data_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", REPO_URL, str(repo_dir)],
                       check=True, capture_output=True)
    return repo_dir

def load_all_entries(repo_dir: Path) -> list[Solution | Tip]:
    entries = []
    entries_dir = repo_dir / "entries"
    if not entries_dir.exists():
        return entries
    for yaml_file in sorted(entries_dir.rglob("*.yaml")):
        try:
            entries.append(load_entry(yaml_file))
        except Exception:
            continue
    return entries
