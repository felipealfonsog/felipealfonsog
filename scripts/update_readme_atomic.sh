#!/usr/bin/env bash
set -euo pipefail

python3 scripts/atomic_sitrep.py > /tmp/atomic_block.txt

START="<!--START_SECTION:atomic_time-->"
END="<!--END_SECTION:atomic_time-->"

awk -v start="$START" -v end="$END" '
BEGIN {inblock=0}
{
  if ($0 ~ start) {
    print $0
    while ((getline line < "/tmp/atomic_block.txt") > 0) print line
    inblock=1
    next
  }
  if ($0 ~ end) {
    inblock=0
    print $0
    next
  }
  if (inblock==0) print $0
}' README.md > README.md.new

mv README.md.new README.md
