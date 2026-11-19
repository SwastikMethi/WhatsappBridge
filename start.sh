#!/usr/bin/env bash
# Start the Python server (FastAPI) and the WhatsApp listener (Baileys) in the background.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p .run

[ -f auth_info_baileys/creds.json ] && linked=1 || linked=0

start() {  # start <name> <command...>
  local name=$1; shift
  if [ -f ".run/$name.pid" ] && kill -0 "$(cat ".run/$name.pid")" 2>/dev/null; then
    echo "$name already running (pid $(cat ".run/$name.pid"))"
    return
  fi
  nohup "$@" >> ".run/$name.log" 2>&1 &
  echo $! > ".run/$name.pid"
  echo "started $name (pid $!), log: .run/$name.log"
}

start api .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8200
start whatsapp node index.mjs

# First run: nothing is linked yet, so show the QR code the listener prints.
if [ "$linked" = 0 ]; then
  echo "Not linked yet. Scan the QR code below from WhatsApp > Linked devices."
  echo "Press Ctrl-C once it says 'opened connection'; the bridge keeps running."
  tail -f .run/whatsapp.log
fi
