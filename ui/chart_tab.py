from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from models.rates import RateSnapshot


class ChartTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.figure = Figure(figsize=(4.6, 3.8), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.canvas)

        self.set_snapshot(None)

    def set_snapshot(self, snapshot: RateSnapshot | None) -> None:
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        axes.set_facecolor("#e9fffb")
        self.figure.patch.set_facecolor("#7fffd4")

        if snapshot is None:
            axes.text(0.5, 0.5, "No current rate loaded", ha="center", va="center", color="#222222")
            axes.set_axis_off()
        else:
            value = float(snapshot.rub_jpy_rate)
            axes.bar(["Current"], [value], color="#ffffff", edgecolor="#111111", linewidth=1.2)
            axes.set_title("Current RUB -> JPY coefficient", color="#222222", fontsize=11)
            axes.set_ylabel("JPY per RUB", color="#222222")
            axes.text(0, value, f"{value:.6f}", ha="center", va="bottom", color="#111111")
            axes.tick_params(colors="#222222")
            axes.spines["top"].set_visible(False)
            axes.spines["right"].set_visible(False)

        self.figure.tight_layout()
        self.canvas.draw_idle()
