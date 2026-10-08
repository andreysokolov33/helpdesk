"""Тесты формулы рейтинга «Лидеры» тренажёра.

Запуск (из корня проекта):
    venv/bin/python -m unittest discover -s tests -t . -v
или, если установлен pytest:
    venv/bin/python -m pytest tests -q
"""

from __future__ import annotations

import unittest

from app.api.v1.routers.helpdesk.training_leaderboard import (
    BAYES_K,
    bayes_score,
    build_leaderboard,
    pool_average,
    raw_percent,
)


class BayesScoreTests(unittest.TestCase):
    def test_default_k_is_20(self) -> None:
        self.assertEqual(BAYES_K, 20)

    def test_single_correct_answer_pulled_to_pool_average(self) -> None:
        # (1 + 20*0.8) / (1 + 20) = 17/21 ≈ 0.8095 → ≈81%
        score = bayes_score(1, 1, p0=0.8)
        self.assertAlmostEqual(score, 17 / 21, places=9)
        self.assertEqual(round(score * 100), 81)

    def test_98_of_100_stays_close_to_raw(self) -> None:
        # (98 + 16) / 120 = 0.95
        score = bayes_score(98, 100, p0=0.8)
        self.assertAlmostEqual(score, 0.95, places=9)

    def test_large_sample_beats_tiny_perfect_sample(self) -> None:
        self.assertGreater(bayes_score(98, 100, p0=0.8), bayes_score(1, 1, p0=0.8))

    def test_zero_answers_equals_prior(self) -> None:
        self.assertAlmostEqual(bayes_score(0, 0, p0=0.8), 0.8)

    def test_k_zero_is_raw_ratio(self) -> None:
        self.assertAlmostEqual(bayes_score(3, 4, p0=0.1, k=0), 0.75)

    def test_invalid_counters_rejected(self) -> None:
        with self.assertRaises(ValueError):
            bayes_score(5, 3, p0=0.5)
        with self.assertRaises(ValueError):
            bayes_score(-1, 3, p0=0.5)


class PoolAverageTests(unittest.TestCase):
    def test_sum_correct_over_sum_total_not_mean_of_percents(self) -> None:
        rows = [{"correct": 1, "total": 1}, {"correct": 0, "total": 9}]
        # mean of percents = 50%, but SUM/SUM = 1/10
        self.assertAlmostEqual(pool_average(rows), 0.1)

    def test_empty_pool(self) -> None:
        self.assertEqual(pool_average([]), 0.0)
        self.assertEqual(pool_average([{"correct": 0, "total": 0}]), 0.0)

    def test_raw_percent(self) -> None:
        self.assertEqual(raw_percent(98, 100), 98.0)
        self.assertEqual(raw_percent(0, 0), 0.0)


class BuildLeaderboardTests(unittest.TestCase):
    def _rows(self) -> list[dict]:
        return [
            {"operator_id": 1, "operator_name": "Анна", "correct": 98, "total": 100, "coverage": 60},
            {"operator_id": 2, "operator_name": "Борис", "correct": 1, "total": 1, "coverage": 1},
            {"operator_id": 3, "operator_name": "Вера", "correct": 0, "total": 0, "coverage": 0},
            {"operator_id": 4, "operator_name": "Глеб", "correct": 61, "total": 99, "coverage": 40},
        ]

    def test_zero_answers_excluded(self) -> None:
        board = build_leaderboard(self._rows())
        ids = [item["operator_id"] for item in board["items"]]
        self.assertNotIn(3, ids)
        self.assertEqual(len(ids), 3)

    def test_p0_is_pool_ratio_of_eligible(self) -> None:
        board = build_leaderboard(self._rows())
        # (98 + 1 + 61) / (100 + 1 + 99) = 160/200 = 80%
        self.assertEqual(board["p0_percent"], 80.0)

    def test_order_and_values(self) -> None:
        board = build_leaderboard(self._rows())
        items = board["items"]
        self.assertEqual([i["operator_id"] for i in items], [1, 2, 4])
        self.assertEqual([i["rank"] for i in items], [1, 2, 3])

        anna, boris, gleb = items
        self.assertEqual(anna["score_percent"], 95.0)
        self.assertEqual(anna["raw_percent"], 98.0)
        self.assertFalse(anna["low_data"])
        self.assertEqual(anna["coverage"], 60)

        self.assertEqual(round(boris["score_percent"]), 81)
        self.assertEqual(boris["raw_percent"], 100.0)
        self.assertTrue(boris["low_data"])

        self.assertLess(gleb["score_percent"], gleb["raw_percent"] + 20)

    def test_low_data_threshold_boundary(self) -> None:
        rows = [
            {"operator_id": 1, "operator_name": "A", "correct": 9, "total": 9},
            {"operator_id": 2, "operator_name": "B", "correct": 9, "total": 10},
        ]
        items = {i["operator_id"]: i for i in build_leaderboard(rows)["items"]}
        self.assertTrue(items[1]["low_data"])
        self.assertFalse(items[2]["low_data"])

    def test_tie_break_by_total_then_name(self) -> None:
        rows = [
            {"operator_id": 1, "operator_name": "Яна", "correct": 5, "total": 10},
            {"operator_id": 2, "operator_name": "Ася", "correct": 5, "total": 10},
            {"operator_id": 3, "operator_name": "Бэлла", "correct": 10, "total": 20},
        ]
        ids = [i["operator_id"] for i in build_leaderboard(rows)["items"]]
        # все с 50% при p0 = 50% → score одинаковый; больше ответов — выше, затем по имени
        self.assertEqual(ids, [3, 2, 1])

    def test_limit(self) -> None:
        board = build_leaderboard(self._rows(), limit=2)
        self.assertEqual(len(board["items"]), 2)

    def test_empty(self) -> None:
        board = build_leaderboard([])
        self.assertEqual(board["items"], [])
        self.assertEqual(board["p0_percent"], 0.0)


if __name__ == "__main__":
    unittest.main()
