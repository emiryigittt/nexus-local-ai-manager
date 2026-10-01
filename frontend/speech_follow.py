"""Follow actual playback; word boundaries when available, estimates otherwise."""

import html
import re

from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtWidgets import QTextEdit


def word_at(text, position_ms, duration_ms, timings=()):
    words = list(re.finditer(r"\S+", text))
    if not words or duration_ms <= 0:
        return -1
    if timings:
        for index, (start, end, _) in enumerate(timings):
            if position_ms < start:
                return max(0, index - 1)
            if position_ms < end:
                return min(index, len(words) - 1)
        return len(words) - 1
    # Local engines expose no word boundaries. Proportional word lengths are an
    # approximation, driven by playback position, never by synthesis completion.
    weights = [max(2, len(word.group())) + (2 if word.group().endswith((".", "!", "?", ",")) else 0) for word in words]
    target = max(0, min(1, position_ms / duration_ms)) * sum(weights)
    elapsed = 0
    for index, weight in enumerate(weights):
        elapsed += weight
        if target < elapsed:
            return index
    return len(words) - 1


class SpeechFollow:
    def __init__(self, window):
        self.window = window
        self.text = ""
        self.timings = []
        self.offset = 0
        self.ranges = []
        self.index = -1

    def reset(self):
        self.text = ""
        self.timings = []
        self.ranges = []
        self.index = -1
        self.offset = 0
        self.window.output_browser.setExtraSelections([])
        self.window.speech_caption.hide()

    def start(self, text, timings=()):
        self.text, self.timings = text, list(timings)
        self.index = -1
        self.ranges = []
        self.remap()
        self.window.speech_caption.setVisible(bool(text))
        self.window.speech_caption.setText(html.escape(text))

    def remap(self):
        if not self.text:
            return
        plain = self.window.output_browser.toPlainText()
        cursor = self.offset
        self.ranges = []
        for token in re.findall(r"\S+", self.text):
            word = token.strip(".,!?;:…\"'()[]")
            match = re.search(re.escape(word), plain[cursor:], re.IGNORECASE) if word else None
            if match:
                start, end = cursor + match.start(), cursor + match.end()
                self.ranges.append((start, end))
                cursor = end
            else:
                self.ranges.append(None)

    def update(self, position):
        index = word_at(self.text, position, self.window.media_player.duration(), self.timings)
        if index < 0:
            return
        self.index = index
        words = self.text.split()
        # A moving caption window avoids clipping a whole paragraph on small screens.
        visible = range(max(0, index - 5), min(len(words), index + 9))
        self.window.speech_caption.setText(" ".join(
            f"<b style='color:#55ef9d'>{html.escape(words[i])}</b>" if i == index else html.escape(words[i])
            for i in visible
        ))
        if index >= len(self.ranges) or self.ranges[index] is None:
            self.window.output_browser.setExtraSelections([])
            return
        start, end = self.ranges[index]
        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(self.window.output_browser.document())
        # Qt text positions count UTF-16 units; Python indexes count code points.
        plain = self.window.output_browser.toPlainText()
        selection.cursor.setPosition(len(plain[:start].encode("utf-16-le")) // 2)
        selection.cursor.setPosition(len(plain[:end].encode("utf-16-le")) // 2, QTextCursor.MoveMode.KeepAnchor)
        selection.format = QTextCharFormat()
        selection.format.setBackground(QColor("#315c46"))
        self.window.output_browser.setExtraSelections([selection])
        block_top = self.window.output_browser.document().documentLayout().blockBoundingRect(selection.cursor.block()).top()
        self.window.output_browser.verticalScrollBar().setValue(max(0, int(block_top) - self.window.output_browser.height() // 3))

    def finish(self):
        matched = [item for item in self.ranges if item is not None]
        if matched:
            self.offset = matched[-1][1]
        self.text = ""
        self.timings = []
        self.ranges = []
        self.window.output_browser.setExtraSelections([])
        self.window.speech_caption.hide()
