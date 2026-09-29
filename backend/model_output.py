"""Filter inline reasoning even when provider tokens split the delimiters."""


class VisibleAnswer:
    def __init__(self):
        self.pending = ""
        self.thinking = False

    def feed(self, text: str, *, final: bool = False) -> str:
        self.pending += text
        output = []
        while self.pending:
            marker = "</think>" if self.thinking else "<think>"
            index = self.pending.lower().find(marker)
            if index >= 0:
                if not self.thinking:
                    output.append(self.pending[:index])
                self.pending = self.pending[index + len(marker):]
                self.thinking = not self.thinking
                continue
            keep = 0
            if not final:
                for length in range(1, min(len(marker), len(self.pending) + 1)):
                    if self.pending.lower().endswith(marker[:length]):
                        keep = length
            visible = self.pending[:-keep] if keep else self.pending
            if not self.thinking:
                output.append(visible)
            self.pending = self.pending[-keep:] if keep else ""
            break
        return "".join(output)
