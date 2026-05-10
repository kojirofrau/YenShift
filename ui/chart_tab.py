from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.dates import AutoDateLocator, DateFormatter
from matplotlib.figure import Figure

from models.rates import RateSnapshot


@dataclass(frozen=True)
class DailyRateAverage:
    day: date
    count: int
    rub_usd_rate: float
    usd_jpy_rate: float
    rub_jpy_rate: float


class ChartTab(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.summary_label = QLabel("No saved rate records")
        self.summary_label.setWordWrap(True)

        self.figure = Figure(figsize=(4.8, 5.0), dpi=100)
        self.canvas = FigureCanvas(self.figure)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.canvas)

        self.set_snapshots([])

    def set_snapshots(self, snapshots: list[RateSnapshot]) -> None:
        self.figure.clear()
        self.figure.patch.set_facecolor("#7fffd4")

        ordered_snapshots = sorted(snapshots, key=lambda snapshot: snapshot.update_time)
        if not ordered_snapshots:
            self.summary_label.setText("No saved rate records")
            axes = self.figure.add_subplot(111)
            axes.set_facecolor("#e9fffb")
            axes.text(0.5, 0.5, "No saved rate data yet", ha="center", va="center", color="#222222")
            axes.set_axis_off()
        else:
            daily_averages = self._average_by_day(ordered_snapshots)
            days = [average.day for average in daily_averages]
            rub_usd_values = [average.rub_usd_rate for average in daily_averages]
            usd_jpy_values = [average.usd_jpy_rate for average in daily_averages]
            rub_jpy_values = [average.rub_jpy_rate for average in daily_averages]
            first_day = daily_averages[0].day.strftime("%Y-%m-%d")
            last_day = daily_averages[-1].day.strftime("%Y-%m-%d")

            self.summary_label.setText(
                f"{len(ordered_snapshots)} saved records averaged into {len(daily_averages)} days "
                f"from {first_day} to {last_day}. Latest daily RUB -> JPY: {rub_jpy_values[-1]:.6f}"
            )

            coefficient_axes = self.figure.add_subplot(311)
            rub_usd_axes = self.figure.add_subplot(312, sharex=coefficient_axes)
            usd_jpy_axes = self.figure.add_subplot(313, sharex=coefficient_axes)
            self._style_axes(coefficient_axes)
            self._style_axes(rub_usd_axes)
            self._style_axes(usd_jpy_axes)

            coefficient_axes.plot(
                days,
                rub_jpy_values,
                color="#111111",
                marker="o",
                linewidth=1.8,
                markersize=4,
            )
            coefficient_axes.fill_between(days, rub_jpy_values, color="#ffffff", alpha=0.38)
            coefficient_axes.set_title("Daily average RUB -> JPY coefficient", color="#222222", fontsize=10)
            coefficient_axes.set_ylabel("JPY per RUB", color="#222222")
            coefficient_axes.annotate(
                f"{rub_jpy_values[-1]:.6f}",
                xy=(days[-1], rub_jpy_values[-1]),
                xytext=(6, 6),
                textcoords="offset points",
                color="#111111",
                fontsize=9,
            )

            rub_usd_axes.plot(
                days,
                rub_usd_values,
                color="#005f73",
                marker="o",
                linewidth=1.5,
                markersize=3,
            )
            rub_usd_axes.set_title("Daily average RUB -> USD", color="#222222", fontsize=10)
            rub_usd_axes.set_ylabel("Rate", color="#222222")
            rub_usd_axes.annotate(
                f"{rub_usd_values[-1]:.4f}",
                xy=(days[-1], rub_usd_values[-1]),
                xytext=(6, 6),
                textcoords="offset points",
                color="#005f73",
                fontsize=9,
            )

            usd_jpy_axes.plot(
                days,
                usd_jpy_values,
                color="#9b2226",
                marker="o",
                linewidth=1.5,
                markersize=3,
            )
            usd_jpy_axes.set_title("Daily average USD -> JPY", color="#222222", fontsize=10)
            usd_jpy_axes.set_ylabel("Rate", color="#222222")
            usd_jpy_axes.annotate(
                f"{usd_jpy_values[-1]:.4f}",
                xy=(days[-1], usd_jpy_values[-1]),
                xytext=(6, 6),
                textcoords="offset points",
                color="#9b2226",
                fontsize=9,
            )

            locator = AutoDateLocator()
            usd_jpy_axes.xaxis.set_major_locator(locator)
            usd_jpy_axes.xaxis.set_major_formatter(DateFormatter("%Y-%m-%d"))
            coefficient_axes.tick_params(labelbottom=False)
            rub_usd_axes.tick_params(labelbottom=False)
            usd_jpy_axes.tick_params(axis="x", rotation=30)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _average_by_day(self, snapshots: list[RateSnapshot]) -> list[DailyRateAverage]:
        grouped_snapshots = defaultdict(list)
        for snapshot in snapshots:
            grouped_snapshots[snapshot.update_time.date()].append(snapshot)

        daily_averages: list[DailyRateAverage] = []
        for day, day_snapshots in sorted(grouped_snapshots.items()):
            count = len(day_snapshots)
            daily_averages.append(
                DailyRateAverage(
                    day=day,
                    count=count,
                    rub_usd_rate=sum(float(snapshot.rub_usd_rate) for snapshot in day_snapshots) / count,
                    usd_jpy_rate=sum(float(snapshot.usd_jpy_rate) for snapshot in day_snapshots) / count,
                    rub_jpy_rate=sum(float(snapshot.rub_jpy_rate) for snapshot in day_snapshots) / count,
                )
            )

        return daily_averages

    def _style_axes(self, axes) -> None:
        axes.set_facecolor("#e9fffb")
        axes.grid(True, color="#b7d8d1", linewidth=0.7, alpha=0.8)
        axes.tick_params(colors="#222222", labelsize=8)
        axes.spines["top"].set_visible(False)
        axes.spines["right"].set_visible(False)
        axes.spines["left"].set_color("#111111")
        axes.spines["bottom"].set_color("#111111")
