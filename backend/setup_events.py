"""Small setup events work even with a Windows executable without a console."""

import json
import os


def report(stage, **values):
    event = json.dumps({"stage": stage, **values}, ensure_ascii=True) + "\n"
    path = os.environ.get("NEXUS_SETUP_EVENTS")
    if path:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(event)
    else:
        print(event, end="", flush=True)
