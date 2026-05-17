from pathlib import Path

from PySide6.QtCore import QThread, Slot
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QMainWindow, QMessageBox, QStackedWidget

from ui.parse_worker import ParseWorker
from ui.views.input_view import InputView
from ui.views.progress_view import ProgressView
from ui.views.results_view import ResultsView

# Conservative reserve for the OS window frame and title bar when capping
# the window to the available screen area. Covers Windows/macOS/Linux
# without per-platform tuning.
_WINDOW_FRAME_RESERVE_W = 20
_WINDOW_FRAME_RESERVE_H = 80


def _default_available_geometry(window):
    screen = window.screen() or QGuiApplication.primaryScreen()
    return screen.availableGeometry()


def _default_worker_factory(character, folder, output):
    return ParseWorker(character, folder, output)


def _default_error_dialog(title, message):
    summary, detail = _split_error_message(message)
    box = QMessageBox(QMessageBox.Warning, title, summary)
    if detail:
        box.setDetailedText(detail)
    box.exec()


def _split_error_message(message):
    text = message or ""
    lower = text.lower()
    if "no such file" in lower or "no log files" in lower or "matching" in lower:
        return (
            "No log files were found for that character in the selected folder. "
            "Double-check the character name (it must match the filename) and "
            "that the folder contains files like eqlog_<Character>_*.txt.",
            text,
        )
    if "permission" in lower or "access is denied" in lower:
        return (
            "The app couldn't read one of the log files. The file may be open "
            "in another program, or you may not have permission to read it.",
            text,
        )
    return (
        "Something went wrong while parsing the logs. The technical details are "
        "below if you want to share them in a bug report.",
        text,
    )


class MainWindow(QMainWindow):
    def __init__(
        self,
        default_log_folder,
        default_output_path,
        default_character_name="",
        worker_factory=None,
        run_worker=None,
        error_dialog=None,
        available_geometry=None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("EverQuest Travel Map")
        self._default_output_path = Path(default_output_path)

        self._worker_factory = worker_factory or _default_worker_factory
        self._run_worker = run_worker or self._run_worker_on_thread
        self._error_dialog = error_dialog or _default_error_dialog
        self._available_geometry = available_geometry or _default_available_geometry

        self._stack = QStackedWidget(self)
        self._stack.setObjectName("rootStack")
        self.setCentralWidget(self._stack)

        self.input_view = InputView(
            default_log_folder=default_log_folder,
            default_output_path=default_output_path,
            default_character_name=default_character_name,
        )
        self.progress_view = ProgressView()
        self.results_view = ResultsView()

        self._stack.addWidget(self.input_view)
        self._stack.addWidget(self.progress_view)
        self._stack.addWidget(self.results_view)

        self._view_by_widget = {
            self.input_view: "input",
            self.progress_view: "progress",
            self.results_view: "results",
        }

        self.input_view.parse_requested.connect(self._on_parse_requested)
        self.progress_view.cancel_requested.connect(self._on_cancel_requested)
        self.results_view.back_requested.connect(self.show_input)

        self._stack.currentChanged.connect(self._resize_to_active_view)

        self._active_worker = None
        self._active_thread = None

        self.show_input()

    # --- view routing ---

    @property
    def current_view_name(self):
        return self._view_by_widget.get(self._stack.currentWidget(), "")

    def show_input(self):
        self._stack.setCurrentWidget(self.input_view)
        self._resize_to_active_view()

    def _resize_to_active_view(self):
        active = self._stack.currentWidget()
        size = getattr(active, "preferred_window_size", None)
        if size is None:
            return
        width, height = size
        # Cap to the active screen's available area minus a reserve for the
        # window frame and title bar. Prevents the results window from
        # overflowing a small display and pushing its title bar off-screen.
        available = self._available_geometry(self)
        width = min(width, max(1, available.width() - _WINDOW_FRAME_RESERVE_W))
        height = min(height, max(1, available.height() - _WINDOW_FRAME_RESERVE_H))
        self.setFixedSize(width, height)
        if not self.isVisible():
            return
        # Re-center on the active screen each time the view changes, so the
        # window never lands off-screen when switching to a larger view.
        new_geom = self.frameGeometry()
        new_geom.moveCenter(available.center())
        self.move(new_geom.topLeft())

    def show_progress(self, character_name):
        self.progress_view.set_character(character_name)
        self.progress_view.reset_progress()
        self._stack.setCurrentWidget(self.progress_view)

    def show_results(self, image_path, summary_sections):
        self.results_view.set_results(image_path, summary_sections)
        self._stack.setCurrentWidget(self.results_view)

    # --- worker wiring ---

    @Slot(str, str, str)
    def _on_parse_requested(self, character, folder, output):
        worker = self._worker_factory(character, folder, output)
        self._active_worker = worker
        worker.totals.connect(self._on_worker_totals)
        worker.progress.connect(self._on_worker_progress)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        worker.canceled.connect(self._on_worker_canceled)
        self.show_progress(character)
        self._run_worker(worker)

    def _run_worker_on_thread(self, worker):
        thread = QThread(self)
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.canceled.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._active_thread = thread
        thread.start()

    @Slot(int)
    def _on_worker_totals(self, total_lines):
        self.progress_view.set_total(total_lines)

    @Slot(str, int)
    def _on_worker_progress(self, file_name, line_count):
        self.progress_view.set_progress(file_name, line_count)

    @Slot(object, object)
    def _on_worker_finished(self, image_path, summary_sections):
        self.show_results(image_path, summary_sections)
        self._clear_worker()

    @Slot(str)
    def _on_worker_error(self, message):
        self.show_input()
        self._error_dialog("Parse failed", message)
        self._clear_worker()

    @Slot()
    def _on_worker_canceled(self):
        self.show_input()
        self._clear_worker()

    @Slot()
    def _on_cancel_requested(self):
        if self._active_worker is not None:
            self._active_worker.cancel()

    def _clear_worker(self):
        self._active_worker = None
        self._active_thread = None
