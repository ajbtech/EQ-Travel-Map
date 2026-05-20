import shutil
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ui.views.more_stats_view import MoreStatsDialog
from ui.widgets.engraved_heading import EngravedHeading
from ui.widgets.map_canvas import MapCanvas
from ui.widgets.parchment_panel import ParchmentPanel
from video_generator import VideoGenerator


class ResultsView(QWidget):
    back_requested = Signal()
    # Target window height. The width is computed from this height in
    # `preferred_window_size` so the window hugs the rendered map + button
    # column with no blank space on the right.
    _PREFERRED_HEIGHT = 700
    # Vertical space the summary stone+parchment takes up: 18px stone bevel
    # + 37px parchment border-image + 95px content + 37px border-image + 18px
    # stone bevel. Drift here if the QSS border-widths change.
    _SUMMARY_TOTAL_HEIGHT = 205
    # Total width of the button column (buttons are setFixedWidth(200), plus
    # the 18px stone bevel on each side).
    _BUTTON_FRAME_WIDTH = 236
    # Matches QFrame#mapFrame border-width in the QSS theme; the bevel paints
    # an 18px stone border on each side of the contained MapCanvas.
    _MAP_FRAME_BORDER = 18
    # Aspect ratio of zone_map.png (2700x1550). Used as a fallback when the
    # rendered map hasn't been loaded yet (e.g. during view construction).
    _FALLBACK_MAP_ASPECT = 2700 / 1550

    @property
    def preferred_window_size(self):
        aspect = self.map_canvas.source_aspect_ratio() or self._FALLBACK_MAP_ASPECT
        border = self._MAP_FRAME_BORDER
        inner_h = self._PREFERRED_HEIGHT - self._SUMMARY_TOTAL_HEIGHT - 2 * border
        map_w = int(round(inner_h * aspect)) + 2 * border
        return (map_w + self._BUTTON_FRAME_WIDTH, self._PREFERRED_HEIGHT)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("resultsView")
        self._current_image_path = None
        self._current_sections = None
        self._zone_list = None
        self._parse_summary = None
        self._video_worker = None
        self._video_offscreen = None
        self._video_dialog = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        upper_row = QHBoxLayout()
        upper_row.setContentsMargins(0, 0, 0, 0)
        upper_row.setSpacing(0)

        self.map_frame = QFrame()
        self.map_frame.setObjectName("mapFrame")
        map_frame_layout = QVBoxLayout(self.map_frame)
        map_frame_layout.setContentsMargins(0, 0, 0, 0)
        self.map_canvas = MapCanvas()
        map_frame_layout.addWidget(self.map_canvas)
        # No stretch on the map frame: its width is driven by
        # _fit_map_frame_to_image() so the stone bevel hugs the rendered
        # map. Trailing stretch (added after the button column) absorbs any
        # leftover horizontal space.
        upper_row.addWidget(self.map_frame)

        self.button_frame = QFrame()
        self.button_frame.setObjectName("buttonFrame")
        button_column = QVBoxLayout(self.button_frame)
        button_column.setContentsMargins(0, 0, 0, 0)
        button_column.setSpacing(8)

        # Match the flat dark-brown Georgia title used on the input screen
        # (QLabel#parchmentTitle in the QSS theme), kept large for the corner.
        self.character_heading = EngravedHeading()
        heading_font = self.character_heading.font()
        heading_font.setPointSize(32)
        self.character_heading.setFont(heading_font)
        self.character_heading.set_color(QColor("#2a1c0e"))
        self.character_heading.set_engraved(False)
        self.character_heading.setFixedWidth(200)
        button_column.addWidget(self.character_heading)

        # Stretch between the heading (pinned top) and the buttons pushes the
        # button stack down to the bottom of the column.
        button_column.addStretch(1)

        self.back_button = QPushButton("NEW INPUT")
        self.back_button.setObjectName("bronzeButton")
        self.back_button.setFixedWidth(200)
        self.back_button.clicked.connect(self.back_requested.emit)
        button_column.addWidget(self.back_button)

        self.copy_text_button = QPushButton("COPY TEXT")
        self.copy_text_button.setObjectName("bronzeButton")
        self.copy_text_button.setFixedWidth(200)
        self.copy_text_button.clicked.connect(self._on_copy_text)
        button_column.addWidget(self.copy_text_button)

        self.save_image_button = QPushButton("SAVE MAP")
        self.save_image_button.setObjectName("bronzeButton")
        self.save_image_button.setFixedWidth(200)
        self.save_image_button.clicked.connect(self._on_save_image)
        button_column.addWidget(self.save_image_button)

        self.more_stats_button = QPushButton("MORE STATS")
        self.more_stats_button.setObjectName("bronzeButton")
        self.more_stats_button.setFixedWidth(200)
        self.more_stats_button.clicked.connect(self._on_more_stats)
        button_column.addWidget(self.more_stats_button)

        self.make_video_button = QPushButton("MAKE VIDEO")
        self.make_video_button.setObjectName("bronzeButton")
        self.make_video_button.setFixedWidth(200)
        self.make_video_button.setEnabled(False)
        self.make_video_button.clicked.connect(self._on_make_video)
        button_column.addWidget(self.make_video_button)

        upper_row.addWidget(self.button_frame)
        upper_row.addStretch(1)

        outer.addLayout(upper_row, 1)

        self.summary_stone_frame = QFrame()
        self.summary_stone_frame.setObjectName("summaryStoneFrame")
        summary_stone_layout = QVBoxLayout(self.summary_stone_frame)
        summary_stone_layout.setContentsMargins(0, 0, 0, 0)
        summary_stone_layout.setSpacing(0)

        summary_parchment = ParchmentPanel()
        summary_parchment.setObjectName("summaryParchment")

        # The columns live in an overlay widget that fills the entire
        # parchment rect (set_fill_child), so text can use the full widget
        # area instead of being squeezed inside the 50px border-image.
        columns_container = QWidget()
        columns_container.setAttribute(Qt.WA_TranslucentBackground)
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setContentsMargins(40, 18, 20, 4)
        columns_layout.setSpacing(12)

        self._kills_column = self._make_column()
        self._zones_column = self._make_column()
        self._stats_column = self._make_column()

        columns_layout.addWidget(self._kills_column, 1, Qt.AlignTop)
        columns_layout.addWidget(self._zones_column, 1, Qt.AlignTop)
        columns_layout.addWidget(self._stats_column, 2, Qt.AlignTop)

        summary_parchment.set_fill_child(columns_container)
        summary_stone_layout.addWidget(summary_parchment)

        # Wrap the summary in an HBox with a trailing stretch so it can be
        # sized to match the upper row's content width (map_frame +
        # button_frame) rather than spanning the full window. The stretch
        # absorbs any leftover space on the right.
        summary_row = QHBoxLayout()
        summary_row.setContentsMargins(0, 0, 0, 0)
        summary_row.setSpacing(0)
        summary_row.addWidget(self.summary_stone_frame)
        summary_row.addStretch(1)
        outer.addLayout(summary_row)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_map_frame_to_image()

    def _fit_map_frame_to_image(self):
        aspect = self.map_canvas.source_aspect_ratio()
        if aspect is None:
            return
        border = self._MAP_FRAME_BORDER
        inner_h = self.map_frame.height() - 2 * border
        if inner_h <= 0:
            return
        target = int(round(inner_h * aspect)) + 2 * border
        if (
            self.map_frame.minimumWidth() != target
            or self.map_frame.maximumWidth() != target
        ):
            self.map_frame.setFixedWidth(target)
        self._fit_summary_to_upper_row()

    def _fit_summary_to_upper_row(self):
        # Span the summary parchment under the map AND the button column so
        # the stone bevels line up on the right.
        summary_w = self.map_frame.width() + self.button_frame.sizeHint().width()
        if (
            self.summary_stone_frame.minimumWidth() != summary_w
            or self.summary_stone_frame.maximumWidth() != summary_w
        ):
            self.summary_stone_frame.setFixedWidth(summary_w)

    def _make_column(self):
        label = QLabel("")
        label.setObjectName("summaryColumn")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        return label

    def set_results(
        self, image_path, summary_sections, zone_list=None, parse_summary=None
    ):
        self._current_image_path = Path(image_path)
        self._current_sections = summary_sections
        self._zone_list = zone_list
        self._parse_summary = parse_summary
        self.map_canvas.load_image(self._current_image_path)
        self.character_heading.setText(self._character_name())
        self._fit_map_frame_to_image()
        self.set_columns(
            summary_sections.top_kills_lines,
            summary_sections.top_zones_lines,
            summary_sections.stats_lines,
        )
        # Restored sessions don't carry a timeline, so video export needs both
        # the zone list and the parsed summary to be present.
        self.make_video_button.setEnabled(
            zone_list is not None and parse_summary is not None
        )

    def set_columns(self, top_kills_lines, top_zones_lines, stats_lines):
        self._kills_column.setText(self._render_column_html(top_kills_lines))
        self._zones_column.setText(self._render_column_html(top_zones_lines))
        self._stats_column.setText(
            self._render_column_html(["Major Statistics", *stats_lines])
        )

    @staticmethod
    def _render_column_html(lines):
        if not lines:
            return ""
        head = f"<b><u>{escape(lines[0])}</u></b>"
        body = [escape(line) for line in lines[1:]]
        return "<br>".join([head, *body])

    def summary_text(self):
        if self._current_sections is None:
            return ""
        parts = []
        if self._current_sections.character_line:
            parts.append(self._current_sections.character_line)
            parts.append("")
        parts.extend(self._current_sections.top_kills_lines)
        parts.append("")
        parts.extend(self._current_sections.top_zones_lines)
        parts.append("")
        parts.extend(self._current_sections.stats_lines)
        return "\n".join(parts)

    def _on_more_stats(self):
        if self._current_sections is None:
            return
        dlg = MoreStatsDialog(self._current_sections, parent=self)
        dlg.show()

    def _on_copy_text(self):
        QGuiApplication.clipboard().setText(self.summary_text())

    def _on_save_image(self):
        if self._current_image_path is None or not self._current_image_path.exists():
            return
        suggested = str(Path.home() / self._suggested_save_filename())
        chosen, _filter = QFileDialog.getSaveFileName(
            self,
            "Save map as",
            suggested,
            "PNG image (*.png);;All files (*)",
        )
        if not chosen:
            return
        shutil.copyfile(self._current_image_path, chosen)

    def _on_make_video(self):
        if self._zone_list is None or self._parse_summary is None:
            return
        if self._current_image_path is None or not self._current_image_path.exists():
            return

        dialog = _DurationDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        target_seconds = dialog.target_seconds()

        suggested = str(Path.home() / self._suggested_video_filename())
        output_path, _filter = QFileDialog.getSaveFileName(
            self, "Save video as", suggested, "MP4 video (*.mp4);;All files (*)"
        )
        if not output_path:
            return

        from ui.video_worker import VideoWorker

        generator = VideoGenerator(
            self._character_name(),
            self._zone_list,
            self._parse_summary,
            target_seconds=target_seconds,
        )

        offscreen = self._build_offscreen_view()

        progress = QProgressDialog(
            "Generating video…", "Cancel", 0, generator.total_frames(), self
        )
        progress.setWindowTitle("Make Video")
        progress.setWindowModality(Qt.WindowModal)
        progress.setAutoClose(False)
        progress.setAutoReset(False)
        progress.setMinimumDuration(0)

        worker = VideoWorker(generator, offscreen, output_path)
        self._video_worker = worker
        self._video_offscreen = offscreen
        self._video_dialog = progress

        worker.progress.connect(lambda current, _total: progress.setValue(current))
        worker.finished.connect(self._on_video_finished)
        worker.error.connect(self._on_video_error)
        worker.canceled.connect(self._on_video_canceled)
        progress.canceled.connect(worker.cancel)

        worker.start()

    def _build_offscreen_view(self):
        offscreen = ResultsView()
        app = QApplication.instance()
        if app is not None:
            offscreen.setStyleSheet(app.styleSheet())
        size = self.size()
        # h.264 with yuv420p needs even dimensions.
        size.setWidth(size.width() - size.width() % 2)
        size.setHeight(size.height() - size.height() % 2)
        offscreen.setAttribute(Qt.WA_DontShowOnScreen, True)
        offscreen.setFixedSize(size)
        offscreen.set_results(self._current_image_path, self._current_sections)
        # Realize the layout offscreen so child widgets get real geometry
        # (without ever appearing on screen) before QWidget.render is called.
        offscreen.show()
        return offscreen

    def _on_video_finished(self, output_path):
        self._close_video_dialog()
        self._cleanup_video()
        QMessageBox.information(self, "Video saved", f"Video saved to:\n{output_path}")

    def _on_video_error(self, message):
        self._close_video_dialog()
        self._cleanup_video()
        QMessageBox.warning(
            self, "Video failed", f"Could not generate the video:\n{message}"
        )

    def _on_video_canceled(self):
        self._close_video_dialog()
        self._cleanup_video()

    def _close_video_dialog(self):
        if self._video_dialog is not None:
            self._video_dialog.close()
            self._video_dialog = None

    def _cleanup_video(self):
        if self._video_offscreen is not None:
            self._video_offscreen.deleteLater()
            self._video_offscreen = None
        self._video_worker = None

    def _suggested_video_filename(self):
        character = self._character_name()
        if character:
            return f"{character}_travel.mp4"
        return "travel.mp4"

    def _suggested_save_filename(self):
        original = self._current_image_path.name
        character = self._character_name()
        if not character:
            return original
        return f"{character}_{original}"

    def _character_name(self):
        if self._current_sections is None:
            return ""
        line = getattr(self._current_sections, "character_line", "")
        prefix = "Character: "
        if line.startswith(prefix):
            return line[len(prefix) :].strip()
        return ""


class _DurationDialog(QDialog):
    """Asks how long the exported video should be, in seconds."""

    _PRESETS = [
        ("30 seconds", 30),
        ("1 minute", 60),
        ("2 minutes", 120),
        ("5 minutes", 300),
    ]
    _DEFAULT_INDEX = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Video length")

        layout = QVBoxLayout(self)
        self._group = QButtonGroup(self)
        for index, (label, seconds) in enumerate(self._PRESETS):
            radio = QRadioButton(label)
            radio.setProperty("seconds", seconds)
            self._group.addButton(radio, index)
            layout.addWidget(radio)
            if index == self._DEFAULT_INDEX:
                radio.setChecked(True)

        custom_row = QHBoxLayout()
        self._custom_radio = QRadioButton("Custom:")
        self._group.addButton(self._custom_radio, len(self._PRESETS))
        self._custom_spin = QSpinBox()
        self._custom_spin.setRange(10, 3600)
        self._custom_spin.setValue(120)
        self._custom_spin.setSuffix(" s")
        custom_row.addWidget(self._custom_radio)
        custom_row.addWidget(self._custom_spin)
        custom_row.addStretch(1)
        layout.addLayout(custom_row)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def target_seconds(self):
        checked = self._group.checkedButton()
        if checked is self._custom_radio:
            return self._custom_spin.value()
        return int(checked.property("seconds"))
