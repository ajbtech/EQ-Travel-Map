"""Tests for the stone-framed parchment helper."""
import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# Make `ui...` imports work the same way the app does.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pytest

from PySide6.QtWidgets import QApplication, QFrame, QVBoxLayout

from ui.widgets.parchment_panel import (
    STONE_FRAME_INSET,
    ParchmentPanel,
    build_stone_framed_parchment,
)


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication(sys.argv)


def test_returns_stone_frame_and_parchment(qapp):
    stone, parchment = build_stone_framed_parchment(
        stone_object_name="testStone",
        parchment_object_name="testParchment",
    )
    assert isinstance(stone, QFrame)
    assert isinstance(parchment, ParchmentPanel)


def test_object_names_are_assigned(qapp):
    stone, parchment = build_stone_framed_parchment(
        stone_object_name="myStone",
        parchment_object_name="myParchment",
    )
    assert stone.objectName() == "myStone"
    assert parchment.objectName() == "myParchment"


def test_parchment_is_child_of_stone_frame(qapp):
    stone, parchment = build_stone_framed_parchment(
        stone_object_name="s", parchment_object_name="p",
    )
    assert parchment.parent() is stone


def test_stone_frame_uses_shared_inset_on_all_sides(qapp):
    stone, _ = build_stone_framed_parchment(
        stone_object_name="s", parchment_object_name="p",
    )
    margins = stone.layout().contentsMargins()
    assert (margins.left(), margins.top(), margins.right(), margins.bottom()) == (
        STONE_FRAME_INSET,
        STONE_FRAME_INSET,
        STONE_FRAME_INSET,
        STONE_FRAME_INSET,
    )


def test_stone_frame_layout_has_no_spacing(qapp):
    stone, _ = build_stone_framed_parchment(
        stone_object_name="s", parchment_object_name="p",
    )
    assert isinstance(stone.layout(), QVBoxLayout)
    assert stone.layout().spacing() == 0
