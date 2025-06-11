"""
Syntax highlighter for JSON used in the MongoDB GUI application.

Provides color highlighting for JSON keys, values, punctuation, numbers, booleans, nulls, and braces.
"""

from PyQt5.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class JsonHighlighter(QSyntaxHighlighter):
    """
    QSyntaxHighlighter subclass for JSON syntax highlighting in PyQt5 text widgets.
    """

    def __init__(self, parent: QTextDocument | None = None) -> None:
        """
        Initialize the JsonHighlighter with color formats and regex patterns.

        Args:
            parent: QTextDocument to apply highlighting to.
        """
        super().__init__(parent)
        self.key_format = QTextCharFormat()
        self.key_format.setForeground(QColor("#007acc"))  # Blue for key with quotes
        self.value_format = QTextCharFormat()
        self.value_format.setForeground(
            QColor("#000000")
        )  # Black for value with quotes
        self.punct_format = QTextCharFormat()
        self.punct_format.setForeground(QColor("#a31515"))  # Red for : and ,
        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#098658"))
        self.bool_format = QTextCharFormat()
        self.bool_format.setForeground(QColor("#795e26"))
        self.null_format = QTextCharFormat()
        self.null_format.setForeground(QColor("#795e26"))
        self.brace_format = QTextCharFormat()
        self.brace_format.setForeground(QColor("#000000"))

        # Pre-compile regular expressions
        import re

        self.key_regex = re.compile(r'"(\\.|[^"\\])*"(?=\s*:)')
        self.punct_regex = re.compile(r"[:,]")
        self.value_regex = re.compile(r'(?<=:)\s*"(\\.|[^"\\])*"')
        self.number_regex = re.compile(r"\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b")
        self.bool_regex = re.compile(r"\btrue\b|\bfalse\b")
        self.null_regex = re.compile(r"\bnull\b")
        self.brace_regex = re.compile(r"[\{\}\[\]]")

    def highlightBlock(self, text: str | None) -> None:
        """
        Apply syntax highlighting to a block of text.

        Args:
            text: The text block to highlight.
        """
        if text is None:
            return
        # Keys ("key") in blue (with quotes)
        for match in self.key_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.key_format)
        # Punctuation : and , in red
        for match in self.punct_regex.finditer(text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.punct_format
            )
        # Values ("value") in black (with quotes, after colon)
        for match in self.value_regex.finditer(text):
            value_match = self.key_regex.search(match.group(0))
            if value_match:
                value_start = match.start() + value_match.start()
                value_len = value_match.end() - value_match.start()
                self.setFormat(value_start, value_len, self.value_format)
        # Numbers
        for match in self.number_regex.finditer(text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.number_format
            )
        # Booleans
        for match in self.bool_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.bool_format)
        # Null
        for match in self.null_regex.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self.null_format)
        # Braces
        for match in self.brace_regex.finditer(text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.brace_format
            )
