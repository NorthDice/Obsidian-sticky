#!/bin/bash
cd "$(dirname "$0")"

if pgrep -f "python3 obsidian_sticky.py" > /dev/null; then
    exit 0
fi

python3 obsidian_sticky.py &
