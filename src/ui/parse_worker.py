from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

import eq_parser
import log_parser
import summary_formatter


class _ParseCanceled(Exception):
    pass


def _default_count(folder, character_name):
    log_files = log_parser.find_log_files(folder, character_name)
    return log_parser.count_lines_in_files(log_files)


class ParseWorker(QObject):
    progress = Signal(str, int)
    totals = Signal(int)
    finished = Signal(object, object)
    error = Signal(str)
    canceled = Signal()

    def __init__(
        self,
        character_name,
        log_folder_path,
        output_path,
        *,
        parse_fn=None,
        draw_fn=None,
        summary_fn=None,
        count_fn=None,
    ):
        super().__init__()
        self.character_name = character_name
        self.log_folder_path = Path(log_folder_path)
        self.output_path = Path(output_path)
        self._parse = parse_fn or log_parser.parse_character_logs
        self._draw = draw_fn or eq_parser.draw_zone_path
        self._build_summary = summary_fn or summary_formatter.build_summary_sections
        self._count = count_fn or _default_count
        self._cancel_requested = False

    @Slot()
    def cancel(self):
        self._cancel_requested = True

    @Slot()
    def run(self):
        try:
            total_lines = self._count(self.log_folder_path, self.character_name)
            self.totals.emit(total_lines)
            if self._cancel_requested:
                raise _ParseCanceled()

            kill_list, zone_list, summary = self._parse(
                self.log_folder_path,
                self.character_name,
                self._on_progress,
            )
            summary_sections = self._build_summary(
                kill_list,
                zone_list,
                summary,
                self.character_name,
            )
            self._draw(zone_list, output_path=self.output_path)
        except _ParseCanceled:
            self.canceled.emit()
            return
        except Exception as exc:
            self.error.emit(str(exc))
            return
        self.finished.emit(self.output_path, summary_sections)

    def _on_progress(self, parse_progress):
        if self._cancel_requested:
            raise _ParseCanceled()
        self.progress.emit(parse_progress.file_path.name, parse_progress.line_count)
