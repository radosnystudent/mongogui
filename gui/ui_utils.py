from PyQt5.QtWidgets import QTextEdit, QTableWidget

def set_minimum_heights(window, min_width=1200, min_height=800):
    if window.width() < min_width or window.height() < min_height:
        window.resize(max(window.width(), min_width), max(window.height(), min_height))
    if hasattr(window, 'query_input') and window.query_input is not None:
        window.query_input.setFixedHeight(max(100, int(window.height() * 0.10)))
    if hasattr(window, 'data_table') and window.data_table is not None:
        try:
            window.data_table.setMinimumHeight(int(window.height() * 0.35))
        except Exception:
            pass
    if hasattr(window, 'result_display') and window.result_display is not None:
        try:
            window.result_display.setMinimumHeight(int(window.height() * 0.35))
        except Exception:
            pass
    window.updateGeometry()
