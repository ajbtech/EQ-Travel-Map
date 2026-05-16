"""End-to-end test against the bundled sample log.

`samples/sample_eqlog_Gorrek_P1999Green.txt` is the documented first-run
experience (see `README.md` and `samples/README.md`). This test pins the
high-level summary counts and confirms `draw_zone_path` produces a
non-empty PNG, so a regression that breaks the real 18k-line log fails
CI rather than being discovered manually.
"""

from pathlib import Path

import eq_parser
import log_parser

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SAMPLE_LOG_FOLDER = PROJECT_ROOT / "samples"
SAMPLE_CHARACTER = "Gorrek"


def test_bundled_sample_log_parses_to_expected_totals():
    _, zone_list, summary = log_parser.parse_character_logs(
        SAMPLE_LOG_FOLDER, SAMPLE_CHARACTER
    )

    assert summary.line_count == 18112
    assert summary.login_count == 668
    assert summary.death_count == 39
    assert summary.zone_count == 1086
    assert summary.kill_count == 5123
    assert summary.level_lost_count == 4
    assert summary.current_level == 51
    assert summary.loot_cash.platinum == 26876
    assert summary.merch_cash.platinum == 9525
    assert len(zone_list.get_raw_eq_list()) == summary.zone_count


def test_bundled_sample_log_renders_a_non_empty_map(tmp_path):
    _, zone_list, _ = log_parser.parse_character_logs(
        SAMPLE_LOG_FOLDER, SAMPLE_CHARACTER
    )
    output_path = tmp_path / "map.png"

    eq_parser.draw_zone_path(zone_list, output_path=output_path)

    assert output_path.exists()
    # The rendered map for an 18k-line log should be substantially larger
    # than the blank zone_map.png header alone; a few hundred KB is the
    # observed range, so 100 KB is a safe lower bound that still catches
    # a regression that produces an empty / black image.
    assert output_path.stat().st_size > 100_000
    assert output_path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
