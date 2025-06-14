from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
import logging


def set_minimum_heights(
    window: QWidget, min_width: int = 1200, min_height: int = 800
) -> None:
    if window.width() < min_width or window.height() < min_height:
        window.resize(max(window.width(), min_width), max(window.height(), min_height))
    if hasattr(window, "query_input") and window.query_input is not None:
        window.query_input.setFixedHeight(max(100, int(window.height() * 0.10)))
    if hasattr(window, "data_table") and window.data_table is not None:
        try:
            window.data_table.setMinimumHeight(int(window.height() * 0.35))
        except Exception as e:
            logging.warning(f"Failed to set minimum height for data_table: {e}")
    if hasattr(window, "result_display") and window.result_display is not None:
        try:
            window.result_display.setMinimumHeight(int(window.height() * 0.35))
        except Exception as e:
            logging.warning(f"Failed to set minimum height for result_display: {e}")
    window.updateGeometry()


def setup_dialog_layout(
    dialog: QDialog,
    widgets: list[QWidget],
    button_widgets: list[QWidget] | None = None,
    layout_cls: type[QVBoxLayout] = QVBoxLayout,
    button_layout_cls: type[QHBoxLayout] = QHBoxLayout,
) -> None:
    """
    Utility to standardize dialog layout setup for QDialog-based forms.

    Args:
        dialog: The QDialog instance.
        widgets: List of widgets to add to the main layout.
        button_widgets: Optional list of widgets (e.g., buttons) to add in a button row.
        layout_cls: Layout class for the main layout (must be QVBoxLayout).
        button_layout_cls: Layout class for the button row (default QHBoxLayout).
    """
    layout = layout_cls(dialog)
    for w in widgets:
        layout.addWidget(w)
    if button_widgets:
        btn_layout = button_layout_cls()
        for btn in button_widgets:
            btn_layout.addWidget(btn)
        # QVBoxLayout supports addLayout
        if isinstance(layout, QVBoxLayout):
            layout.addLayout(btn_layout)
        else:
            raise TypeError(
                "setup_dialog_layout requires main layout to be QVBoxLayout if using button_widgets."
            )
    dialog.setLayout(layout)
