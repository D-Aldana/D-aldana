#!/usr/bin/env python3
"""Tests for build.py. Run with: python3 scripts/test_build.py"""
import os
import sys
import unittest
import xml.dom.minidom as minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build


class TestEscaping(unittest.TestCase):
    def test_x_escapes_special_chars(self):
        self.assertEqual(build.x('<a> & "b"'), "&lt;a&gt; &amp; &quot;b&quot;")

    def test_x_stringifies_non_str(self):
        self.assertEqual(build.x(42), "42")


class TestPct(unittest.TestCase):
    def test_midpoint(self):
        self.assertEqual(build.pct(5, 10), "50.000%")

    def test_clamps_below_zero(self):
        self.assertEqual(build.pct(-5, 10), "0.000%")

    def test_clamps_above_total(self):
        self.assertEqual(build.pct(15, 10), "100.000%")


class TestComputeStreak(unittest.TestCase):
    def test_no_contributions(self):
        self.assertEqual(build.compute_streak([0, 0, 0]), (0, 0))

    def test_active_streak_ending_today(self):
        self.assertEqual(build.compute_streak([1, 1, 1]), (3, 3))

    def test_active_streak_with_leading_quiet_day(self):
        self.assertEqual(build.compute_streak([0, 1, 1, 1, 1]), (4, 4))

    def test_today_empty_does_not_break_streak(self):
        current, _ = build.compute_streak([1, 1, 1, 0])
        self.assertEqual(current, 3)

    def test_longest_can_exceed_current(self):
        current, longest = build.compute_streak([1, 1, 1, 1, 0, 0, 1])
        self.assertEqual(current, 1)
        self.assertEqual(longest, 4)

    def test_gap_breaks_streak(self):
        self.assertEqual(build.compute_streak([1, 0, 1, 1]), (2, 2))

    def test_empty_input(self):
        self.assertEqual(build.compute_streak([]), (0, 0))


class TestRenderSvgCards(unittest.TestCase):
    def _assert_well_formed(self, svg):
        minidom.parseString(svg)

    def test_render_pipeline_is_well_formed_svg(self):
        svg = build.render_pipeline()
        self.assertTrue(svg.startswith("<svg"))
        self._assert_well_formed(svg)
        self.assertIn("Architect", svg)

    def test_render_stack_is_well_formed_svg(self):
        svg = build.render_stack()
        self._assert_well_formed(svg)
        self.assertIn("TypeScript", svg)

    def test_render_terminal_is_well_formed_svg(self):
        svg = build.render_terminal(build.SAMPLE)
        self._assert_well_formed(svg)
        self.assertIn(build.NAME, svg)

    def test_render_streak_is_well_formed_svg(self):
        svg = build.render_streak(build.SAMPLE)
        self._assert_well_formed(svg)
        self.assertIn(f'{build.SAMPLE["streak"]} day', svg)

    def test_render_streak_square_count_matches_window(self):
        svg = build.render_streak(build.SAMPLE)
        self.assertEqual(svg.count('<rect class="sq'), len(build.SAMPLE["last30"]))


class TestFetchStats(unittest.TestCase):
    def test_returns_none_without_token(self):
        old = os.environ.pop("GITHUB_TOKEN", None)
        try:
            self.assertIsNone(build.fetch_stats())
        finally:
            if old is not None:
                os.environ["GITHUB_TOKEN"] = old


if __name__ == "__main__":
    unittest.main()
