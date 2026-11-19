#!/usr/bin/env bash
# Stop what start.sh started.
cd "$(dirname "$0")"

for name in whatsapp api; do
  pid=$(cat ".run/$name.pid" 2>/dev/null) || { echo "$name not running"; continue; }
  kill "$pid" 2>/dev/null && echo "stopped $name (pid $pid)" || echo "$name was not running"
  rm -f ".run/$name.pid"
done
