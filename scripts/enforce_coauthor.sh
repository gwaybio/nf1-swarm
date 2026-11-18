#!/usr/bin/env bash
# commit-msg hook: enforce Co-authored-by trailer on all bot commits.
# Human commits (from gwaybio) are exempt.
# Install: this file must be at .git/hooks/commit-msg and be executable.
# It is also written to scripts/enforce_coauthor.sh for reference.

COMMIT_MSG_FILE="$1"
MSG=$(cat "$COMMIT_MSG_FILE")

# Get the committer identity
AUTHOR_EMAIL=$(git config user.email)

# Exempt real human commits
if [[ "$AUTHOR_EMAIL" == "gregory.way@gmail.com" ]]; then
  exit 0
fi

# Check for co-author trailer
if echo "$MSG" | grep -q "Co-authored-by: Gregory Way <gregory.way@gmail.com>"; then
  exit 0
fi

echo ""
echo "ERROR: missing Co-authored-by trailer."
echo "All bot commits must include:"
echo ""
echo "  Co-authored-by: Gregory Way <gregory.way@gmail.com>"
echo ""
echo "Add it to your commit message and retry."
echo "The commit template at .github/commit_template.txt handles this"
echo "automatically when you use 'git commit' without -m."
echo "When using -m, append the trailer manually."
exit 1
