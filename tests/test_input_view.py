from ui.views.input_view import InputView


def _make_view(tmp_path, character="Gorrek"):
    return InputView(
        default_log_folder=tmp_path,
        default_output_path=tmp_path / "out.png",
        default_character_name=character,
    )


def test_generate_blocked_when_no_log_files_match(qt_app, tmp_path):
    view = _make_view(tmp_path)
    emitted = []
    view.parse_requested.connect(lambda *args: emitted.append(args))

    view._on_generate_clicked()

    assert emitted == []
    assert not view.error_label.isHidden()
    text = view.error_label.text()
    assert "Gorrek" in text
    assert "log file" in text.lower()


def test_generate_emits_when_log_file_exists(qt_app, tmp_path):
    (tmp_path / "eqlog_Gorrek_P1999Green.txt").write_text("", encoding="utf-8")
    view = _make_view(tmp_path)
    emitted = []
    view.parse_requested.connect(lambda *args: emitted.append(args))

    view._on_generate_clicked()

    assert len(emitted) == 1
    character, folder, _output = emitted[0]
    assert character == "Gorrek"
    assert folder == str(tmp_path)
    assert view.error_label.isHidden()


def test_other_characters_logs_do_not_count_as_match(qt_app, tmp_path):
    (tmp_path / "eqlog_Mortimer_P1999Green.txt").write_text("", encoding="utf-8")
    view = _make_view(tmp_path, character="Gorrek")
    emitted = []
    view.parse_requested.connect(lambda *args: emitted.append(args))

    view._on_generate_clicked()

    assert emitted == []
    assert not view.error_label.isHidden()
    assert "Gorrek" in view.error_label.text()
