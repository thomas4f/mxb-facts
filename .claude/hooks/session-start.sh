#!/bin/bash
# Cloud sessions: install what the checks and the analyses need, skipping what is already done.
set -euo pipefail
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi
cd "${CLAUDE_PROJECT_DIR:-.}"

# Python packages for site/build.py and the tools (requirements.txt pins them).
pyhashes="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.session-start.sha256"
if ! sha256sum --check --status "$pyhashes" 2>/dev/null; then
  rm -f "$pyhashes"
  python3 -m pip install -q -r requirements.txt
  sha256sum "$PWD/requirements.txt" > "$pyhashes" || rm -f "$pyhashes"
fi

# Plugin test host: Wine, MinGW, Xvfb, strace, the built host and a smoke test (CLAUDE.md, "How to analyse").
lab/plugin-test-host/setup.sh
