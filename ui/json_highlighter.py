from PyQt5.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat, QTextDocument


class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent: QTextDocument | None = None) -> None:
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

    def highlightBlock(self, text: str | None) -> None:
        import re

        if text is None:
            return
        # Keys ("key") in blue (with quotes)
        for match in re.finditer(r'"(\\.|[^"\\])*"(?=\s*:)', text):
            self.setFormat(match.start(), match.end() - match.start(), self.key_format)
        # Punctuation : and , in red
        for match in re.finditer(r"[:,]", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.punct_format
            )
        # Values ("value") in black (with quotes, after colon)
        for match in re.finditer(r'(?<=:)\s*"(\\.|[^"\\])*"', text):
            value_match = re.search(r'"(\\.|[^"\\])*"', match.group(0))
            if value_match:
                value_start = match.start() + value_match.start()
                value_len = value_match.end() - value_match.start()
                self.setFormat(value_start, value_len, self.value_format)
        # Numbers
        for match in re.finditer(r"\b-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.number_format
            )
        # Booleans
        for match in re.finditer(r"\btrue\b|\bfalse\b", text):
            self.setFormat(match.start(), match.end() - match.start(), self.bool_format)
        # Null
        for match in re.finditer(r"\bnull\b", text):
            self.setFormat(match.start(), match.end() - match.start(), self.null_format)
        # Braces
        for match in re.finditer(r"[\{\}\[\]]", text):
            self.setFormat(
                match.start(), match.end() - match.start(), self.brace_format
            )
