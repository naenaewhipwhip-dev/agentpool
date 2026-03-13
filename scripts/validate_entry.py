#!/usr/bin/env python3
"""Validate YAML entries against the AgentPool schema."""
import sys
from pathlib import Path
import yaml
from agentpool.models import validate_entry

errors = []
entries_dir = Path("entries")

if not entries_dir.exists():
    print("✓ No entries directory found (nothing to validate)")
    sys.exit(0)

count = 0
for path in sorted(entries_dir.rglob("*.yaml")):
    try:
        data = yaml.safe_load(path.read_text())
        validate_entry(data)
        count += 1
    except Exception as e:
        errors.append(f"{path}: {e}")

if errors:
    for e in errors:
        print(f"❌ {e}", file=sys.stderr)
    sys.exit(1)

print(f"✓ {count} entries validated successfully")
