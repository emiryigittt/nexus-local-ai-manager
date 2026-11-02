"""MCP fixture that talks on stderr, the way an npx-launched server does.

Pass ``--hang`` as the first argument to get a server that logs once and then
reads stdin without ever replying, which is how a wedged server looks to the
client.
"""

import json
import sys
import time

HANG = "--hang" in sys.argv

sys.stderr.write("MCP_NOISE_MARKER\n")
sys.stderr.flush()

if not HANG:
    # Far more than an OS pipe buffer holds, written in a handful of calls. A
    # client that never reads this pipe leaves the child blocked in write(2), so
    # the session never gets a reply; a client that drains reaches the marker.
    block = "".join(f"noise {index}\n" for index in range(20_000))
    for _ in range(8):
        sys.stderr.write(block)
    sys.stderr.write("NOISE_DRAIN_COMPLETE\n")
    sys.stderr.flush()

for line in sys.stdin:
    if HANG:
        time.sleep(0.1)
        continue
    message = json.loads(line)
    if "id" not in message:
        continue
    method = message.get("method")
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "noisy", "version": "1"},
        }
    elif method == "tools/list":
        result = {"tools": [{"name": "echo", "description": "Echo", "inputSchema": {}}]}
    else:
        result = {}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
