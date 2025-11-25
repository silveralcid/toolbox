#!/usr/bin/env bash

ROOT="${1:-$(pwd)}"

echo "Using directory: $ROOT"

find "$ROOT" -type d | while read -r dir; do
    subdirs=$(find "$dir" -mindepth 1 -maxdepth 1 -type d | wc -l)
    files=$(find "$dir" -mindepth 1 -maxdepth 1 -type f | wc -l)

    if [ "$subdirs" -eq 0 ] && [ "$files" -eq 0 ]; then
        gitkeep="$dir/.gitkeep"
        if [ ! -f "$gitkeep" ]; then
            touch "$gitkeep"
            echo "Created: $gitkeep"
        fi
    fi
done
