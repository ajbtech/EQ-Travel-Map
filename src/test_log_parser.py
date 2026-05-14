from datetime import datetime

import log_parser


def test_parse_character_logs_with_no_matching_files_returns_empty_summary(tmp_path):
    _, zone_list, summary = log_parser.parse_character_logs(tmp_path, "Missing")

    assert zone_list.get_raw_eq_list() == []
    assert summary.line_count == 0
    assert summary.current_level == 1


def test_parse_log_files_ignores_empty_files_mixed_with_real_files(tmp_path):
    empty_log = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    real_log = tmp_path / "ARCHIVE2eqlog_Gorrek_P1999Green.txt"
    empty_log.write_text("")
    real_log.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sun Jan 08 15:01:29 2023] You have entered Lake Rathetear.\n"
    )

    _, zone_list, summary = log_parser.parse_log_files([empty_log, real_log])

    assert summary.line_count == 2
    assert summary.login_count == 1
    assert zone_list.get_raw_eq_list() == ["Lake Rathetear"]


def test_get_first_log_timestamp_returns_max_when_file_has_no_timestamp(tmp_path):
    log_file = tmp_path / "eqlog_Gorrek_P1999Green.txt"
    log_file.write_text("This line has no timestamp.\n")

    assert log_parser.get_first_log_timestamp(log_file) == datetime.max


def test_parse_log_lines_tracks_first_login_and_most_recent_message():
    lines = [
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!",
        "[Sat Sep 24 19:52:00 2022] You have entered Grobb.",
        "[Sat Sep 24 19:53:00 2022] You say, 'hello'",
    ]

    _, _, summary = log_parser.parse_log_lines(lines)

    assert summary.first_login_message == lines[0]
    assert summary.most_recent_message == lines[-1]


def test_parse_log_files_reports_progress(monkeypatch, tmp_path):
    monkeypatch.setattr(log_parser, "PROGRESS_LINE_INTERVAL", 2)
    log_file = tmp_path / "ARCHIVEeqlog_Gorrek_P1999Green.txt"
    log_file.write_text(
        "[Sat Sep 24 19:51:48 2022] Welcome to EverQuest!\n"
        "[Sat Sep 24 19:52:00 2022] You have entered Grobb.\n"
        "[Sat Sep 24 19:53:00 2022] You say, 'hello'\n"
        "[Sat Sep 24 19:54:00 2022] You say, 'still here'\n"
        "[Sat Sep 24 19:55:00 2022] You say, 'done'\n"
    )
    progress_updates = []

    log_parser.parse_log_files([log_file], progress_updates.append)

    assert progress_updates[0] == log_parser.ParseProgress(log_file, 0)
    assert log_parser.ParseProgress(log_file, 2) in progress_updates
    assert log_parser.ParseProgress(log_file, 4) in progress_updates
    assert progress_updates[-1] == log_parser.ParseProgress(log_file, 5)
