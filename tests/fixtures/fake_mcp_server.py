import json
import sys

for line in sys.stdin:
    message = json.loads(line)
    if "id" not in message:
        continue
    method = message.get("method")
    if method == "initialize":
        result = {
            "protocolVersion": "2025-06-18",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "fake", "version": "1"},
        }
    elif method == "tools/list":
        result = {
            "tools": [
                {
                    "name": "echo",
                    "description": "Echo a value",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"value": {"type": "string"}},
                    },
                }
            ]
        }
    elif method == "tools/call":
        value = message.get("params", {}).get("arguments", {}).get("value", "")
        result = {"content": [{"type": "text", "text": value}]}
    else:
        result = {}
    print(json.dumps({"jsonrpc": "2.0", "id": message["id"], "result": result}), flush=True)
