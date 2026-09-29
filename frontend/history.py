class PromptHistory:
    """Manages a history of prompts for navigation."""

    def __init__(self, max_history=50):
        """Initialize the prompt history.

        Args:
            max_history (int): The maximum number of items to store in history.
        """
        self.history = []
        self.index = -1
        self.max_history = max_history

    def add(self, text: str) -> None:
        """Add a new prompt to the history.

        Strips whitespace from the input text and ignores it if empty.
        If the history is empty or the last item differs from the current text,
        the text is appended. The history is trimmed to max_history size.
        The index is updated to point to the newly added item.

        Args:
            text (str): The text to add to history.
        """
        stripped_text = text.strip()
        if not stripped_text:
            return

        # Append only if history is empty or last item is different
        if not self.history or self.history[-1] != stripped_text:
            self.history.append(stripped_text)

            # Trim to max_history (remove oldest items from the start)
            if len(self.history) > self.max_history:
                self.history = self.history[-self.max_history:]

        # Update index to point to the newly added item
        self.index = len(self.history)

    def get_previous(self) -> str:
        """Get the previous prompt in history.

        Returns:
            str: The previous prompt, or an empty string if history is empty.
        """
        if not self.history:
            return ''

        # Decrement index, ensuring it does not go below 0
        self.index = max(0, self.index - 1)
        return self.history[self.index]

    def get_next(self) -> str:
        """Get the next prompt in history.

        Returns:
            str: The next prompt, or an empty string if at the end of history.
        """
        if not self.history:
            return ''

        # If we are not at the last item, move forward
        if self.index < len(self.history) - 1:
            self.index += 1
            return self.history[self.index]
        else:
            # We are at the last item; clear input pointer and return empty string
            self.index = len(self.history)
            return ''

    def is_empty(self) -> bool:
        """Check if history is empty.

        Returns:
            bool: True if history has no items, False otherwise.
        """
        return len(self.history) == 0
