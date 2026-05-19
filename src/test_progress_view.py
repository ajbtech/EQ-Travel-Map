from ui.views.progress_view import ProgressView


def test_progress_view_initializes_without_error(qt_app):
    view = ProgressView()
    assert view is not None


def test_set_character_updates_label(qt_app):
    view = ProgressView()
    view.set_character("Gorrek")
    assert "Gorrek" in view.character_label.text()


def test_reset_progress_clears_bar_and_labels(qt_app):
    view = ProgressView()
    view.set_total(1000)
    view.set_progress("some_file.txt", 500)
    view.reset_progress()
    assert view.progress_bar.maximum() == 0
    assert "0" in view.lines_label.text()


def test_set_total_enables_determinate_progress(qt_app):
    view = ProgressView()
    view.set_total(5000)
    assert view.progress_bar.maximum() == 5000


def test_set_total_zero_keeps_indeterminate(qt_app):
    view = ProgressView()
    view.set_total(0)
    assert view.progress_bar.maximum() == 0


def test_set_progress_updates_file_and_line_labels(qt_app):
    view = ProgressView()
    view.set_total(100)
    view.set_progress("myfile.txt", 50)
    assert "myfile.txt" in view.file_label.text()
    assert "50" in view.lines_label.text()


def test_lines_label_left_edge_is_stable_and_text_not_clipped(qt_app):
    view = ProgressView()
    view.resize(720, 360)
    view.show()
    view.set_total(0)
    view.set_progress("file.txt", 1)
    qt_app.processEvents()
    small_x = view.lines_label.mapTo(view, view.lines_label.rect().topLeft()).x()
    view.set_progress("file.txt", 999_999_999)
    qt_app.processEvents()
    large_x = view.lines_label.mapTo(view, view.lines_label.rect().topLeft()).x()
    assert small_x == large_x
    natural = view.lines_label.sizeHint().width()
    assert view.lines_label.width() >= natural


def test_lines_label_left_of_cancel_button_with_gap(qt_app):
    view = ProgressView()
    view.resize(720, 360)
    view.show()
    view.set_progress("file.txt", 999_999_999)
    label_left = view.lines_label.mapTo(view, view.lines_label.rect().topLeft()).x()
    label_right = label_left + view.lines_label.width()
    button = view.cancel_button
    button_left = button.mapTo(view, button.rect().topLeft()).x()
    button_right = button_left + button.width()
    assert label_left < 80
    assert label_right <= button_left
    assert button_right >= view.width() - 80


def test_cancel_button_emits_cancel_requested(qt_app):
    view = ProgressView()
    received = []
    view.cancel_requested.connect(lambda: received.append(True))
    view.cancel_button.click()
    assert received == [True]
