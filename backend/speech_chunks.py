"""Bound streaming TTS work without waiting for an arbitrarily long sentence."""

import re


def take_speech_chunks(buffer: str, *, flush=False, limit=180):
    chunks = []
    while buffer.strip():
        # Skip numeric decimal points and numbered-list prefixes.
        match = re.search(r"(?<=[.!?…])\s+|\n+", buffer)
        end = match.end() if match else 0
        if end and buffer[:end].strip().rstrip(".").isdigit():
            match = re.search(r"(?<=[.!?…])\s+|\n+", buffer[end:])
            end = end + match.end() if match else 0
        if not end or end > limit:
            if len(buffer) >= limit or flush:
                boundary = min(limit, len(buffer))
                soft = list(re.finditer(r"[,;:]\s+", buffer[:boundary]))
                end = len(buffer) if flush and len(buffer) <= limit else (
                    soft[-1].end() if soft and soft[-1].end() >= 50 else buffer.rfind(" ", 0, boundary + 1)
                )
                if end < 1:
                    end = boundary
            if not end:
                break
        chunk = buffer[:end].strip()
        buffer = buffer[end:].lstrip()
        if chunk:
            chunks.append(chunk)
    if flush and buffer.strip():
        chunks.append(buffer.strip())
        buffer = ""
    return chunks, buffer
