from __future__ import annotations
import re
from pathlib import Path
from agentpool.models import Solution, Tip


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")


def create_entry_file(
    output_dir: Path,
    entry_type: str,
    title: str,
    tags: list[str] | None = None,
    problem: str = "",
    solution: str = "",
    content: str = "",
) -> Path:
    tags = tags or []
    slug = slugify(title)

    if entry_type == "solution":
        entry = Solution(title=title, problem=problem, solution=solution, tags=tags)
        subdir = output_dir / "entries" / "solutions"
    else:
        entry = Tip(title=title, content=content, tags=tags)
        subdir = output_dir / "entries" / "tips"

    subdir.mkdir(parents=True, exist_ok=True)
    path = subdir / f"{slug}.yaml"
    path.write_text(entry.to_yaml())
    return path
