#!/usr/bin/env python3
"""
Export relevant gems from Qdrant gems_tr to AgentPool YAML entries.

Usage:
    ssh -L 6333:127.0.0.1:6333 macmini -N &
    python scripts/export_gems.py --output entries/ --limit 150
"""
import argparse
import re
import uuid
from datetime import date
from pathlib import Path

import requests
import yaml

QDRANT_URL = "http://127.0.0.1:6333"
COLLECTION = "gems_tr"
BATCH_SIZE = 100

INCLUDE_KEYWORDS = [
    "agent", "mcp", "openclaw", "litellm", "qdrant", "chromadb",
    "tool", "prompt", "context", "embedding", "model", "llm",
    "kubernetes", "k3s", "docker", "launchd", "deployment",
    "rate limit", "backoff", "retry", "error", "debug",
    "memory", "vector", "search", "plugin", "extension",
    "discord", "mattermost", "webhook", "api", "auth",
    "config", "yaml", "json", "git", "worktree",
    "cost", "token", "budget", "routing", "fallback",
    "cron", "schedule", "automation", "script",
]

EXCLUDE_KEYWORDS = [
    "password", "secret", "token sk-", "api_key", "apikey",
    "phone number", "address", "ssn", "credit card",
    "maren", "girlfriend", "personal",
]


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text.strip("-")[:80]


def get_existing_titles(entries_dir: Path) -> set[str]:
    titles = set()
    for f in entries_dir.rglob("*.yaml"):
        try:
            data = yaml.safe_load(f.read_text())
            if data and "title" in data:
                titles.add(data["title"].lower().strip())
        except Exception:
            continue
    return titles


def scroll_gems(qdrant_url: str) -> list[dict]:
    gems = []
    offset = None
    while True:
        body = {"limit": BATCH_SIZE, "with_payload": True, "with_vector": False}
        if offset is not None:
            body["offset"] = offset
        resp = requests.post(
            f"{qdrant_url}/collections/{COLLECTION}/points/scroll",
            json=body,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()["result"]
        points = data.get("points", [])
        if not points:
            break
        gems.extend(points)
        offset = data.get("next_page_offset")
        if offset is None:
            break
    return gems


def is_relevant(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in INCLUDE_KEYWORDS)


def is_private(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in EXCLUDE_KEYWORDS)


def extract_tags(text: str) -> list[str]:
    lower = text.lower()
    tags = []
    tag_map = {
        "openclaw": "openclaw", "mcp": "mcp", "litellm": "litellm",
        "qdrant": "qdrant", "chromadb": "chromadb", "kubernetes": "kubernetes",
        "k3s": "k3s", "docker": "docker", "launchd": "launchd",
        "discord": "discord", "mattermost": "mattermost", "agent": "agents",
        "embedding": "embeddings", "vector": "vector-db", "prompt": "prompting",
        "rate limit": "rate-limiting", "backoff": "retry", "git": "git",
        "cost": "cost-optimization", "token": "context-window",
        "memory": "memory", "cron": "automation", "fastmcp": "fastmcp",
        "python": "python", "typescript": "typescript",
    }
    for keyword, tag in tag_map.items():
        if keyword in lower and tag not in tags:
            tags.append(tag)
    return tags[:8]


def gem_to_entry(payload: dict) -> dict | None:
    gem = payload.get("gem") or payload.get("content") or payload.get("text") or ""
    context = payload.get("context") or ""
    snippet = payload.get("snippet") or ""
    categories = payload.get("categories") or []
    importance = payload.get("importance") or "medium"

    if not gem or len(gem) < 20:
        return None

    # Build full text for relevance/privacy checks
    full_text = f"{gem} {context} {snippet}"
    if not is_relevant(full_text) or is_private(full_text):
        return None

    # Determine type from categories: trap/lesson -> solution, fact/tip -> tip
    solution_categories = {"trap", "lesson", "fix", "workaround"}
    is_solution = bool(solution_categories.intersection(set(categories)))

    # Also check text markers as fallback
    if not is_solution:
        lower = gem.lower()
        is_solution = any(marker in lower for marker in [
            "problem:", "fix:", "workaround:", "root cause:",
            "the issue was", "the fix was", "resolved by",
        ])

    # Build tags from all text
    tags = extract_tags(full_text)
    # High importance gems get a tag
    if importance == "high" and "high-value" not in tags:
        tags = ["high-value"] + tags
    tags = tags[:8]

    title = gem[:120].strip()

    if is_solution:
        # problem = context (what went wrong), solution = gem (the insight/fix)
        problem = context.strip() if context else snippet.strip() if snippet else "See solution."
        solution = gem.strip()
        if snippet and snippet.strip() != solution:
            solution = f"{solution}\n\nExample:\n{snippet.strip()}"
        return {
            "type": "solution",
            "title": title,
            "problem": problem,
            "solution": solution,
            "tags": tags,
        }
    else:
        # tip: gem is the insight, context adds detail
        content = gem.strip()
        if context and context.strip() != content:
            content = f"{content}\n\nContext:\n{context.strip()}"
        if snippet and snippet.strip() not in content:
            content = f"{content}\n\nExample:\n{snippet.strip()}"
        return {
            "type": "tip",
            "title": title,
            "content": content,
            "tags": tags,
        }


def main():
    parser = argparse.ArgumentParser(description="Export Qdrant gems to AgentPool entries")
    parser.add_argument("--qdrant-url", default=QDRANT_URL)
    parser.add_argument("--output", default="entries", help="Output directory")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=150)
    args = parser.parse_args()

    output_dir = Path(args.output)
    existing_titles = get_existing_titles(output_dir)
    print(f"Found {len(existing_titles)} existing entries")

    print(f"Scrolling gems from {args.qdrant_url}...")
    gems = scroll_gems(args.qdrant_url)
    print(f"Fetched {len(gems)} gems")

    created = 0
    skipped_dup = 0
    skipped_irrelevant = 0

    for gem in gems:
        if created >= args.limit:
            break
        payload = gem.get("payload", {})
        entry = gem_to_entry(payload)
        if entry is None:
            skipped_irrelevant += 1
            continue
        if entry["title"].lower().strip() in existing_titles:
            skipped_dup += 1
            continue

        prefix = "sol" if entry["type"] == "solution" else "tip"
        entry["id"] = f"{prefix}-{uuid.uuid4().hex[:8]}"
        entry["contributor"] = "gems-export"
        entry["created"] = str(date.today())
        entry["votes"] = 0
        entry["frameworks"] = []

        slug = slugify(entry["title"])
        if not slug:
            slug = entry["id"]
        subdir = "solutions" if entry["type"] == "solution" else "tips"
        path = output_dir / subdir / f"{slug}.yaml"

        if path.exists():
            skipped_dup += 1
            continue

        if args.dry_run:
            print(f"  [{entry['type']}] {entry['title'][:80]}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(yaml.dump(entry, default_flow_style=False, sort_keys=False, allow_unicode=True))

        existing_titles.add(entry["title"].lower().strip())
        created += 1

    print(f"\nDone: {created} created, {skipped_dup} duplicates, {skipped_irrelevant} irrelevant")


if __name__ == "__main__":
    main()
