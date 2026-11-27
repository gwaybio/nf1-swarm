#!/usr/bin/env python3
"""Check Cypher files for semicolons inside string literals (breaks naive splitter)."""
import re
import sys
from pathlib import Path

errors = []
for f in Path(".").rglob("*.cypher"):
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if re.search(r"'[^']*;[^']*'", line):
            errors.append(f"{f}:{i}: semicolon inside string: {line.strip()!r}")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
print("  OK  no semicolons inside Cypher string literals")
