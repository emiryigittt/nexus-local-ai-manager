"""Generate Nexus's original, short, gently enveloped PCM chimes using only stdlib."""

import math
import struct
import wave
from pathlib import Path

OUTPUT = Path(__file__).resolve().parents[1] / "frontend/assets/sounds"
NOTES = {"open": [523, 784], "collapse": [659, 440], "success": [523, 659, 784],
         "attachment": [587, 740], "error": [349, 330], "listen": [440, 659]}


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, notes in NOTES.items():
        samples = []
        for frequency in notes:
            for index in range(3528):
                progress = index / 3528
                envelope = math.sin(math.pi * progress) ** 2
                value = .24 * envelope * (math.sin(math.tau * frequency * index / 44100)
                                         + .12 * math.sin(math.tau * frequency * 2 * index / 44100))
                samples.append(struct.pack("<h", int(value * 32767)))
        with wave.open(str(OUTPUT / f"{name}.wav"), "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(44100)
            audio.writeframes(b"".join(samples))


if __name__ == "__main__":
    main()
