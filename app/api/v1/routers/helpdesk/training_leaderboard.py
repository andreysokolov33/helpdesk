"""Рейтинг «Лидеры» тренажёра — чистые функции без БД.

Считаем по ответам за период: сырой результат = SUM(correct) / SUM(total),
а не среднее процентов по сессиям.

Ранжирование — байесовское сглаживание к среднему по выборке:

    score = (correct + k * p0) / (total + k)

где k = 20 («вес» априорного среднего в ответах), p0 = SUM(correct) / SUM(total)
по всем сотрудникам выборки за период. Порога нет: в рейтинг попадают все,
у кого есть хотя бы один ответ; при total < LOW_DATA_THRESHOLD — пометка «мало данных».
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

BAYES_K = 20
LOW_DATA_THRESHOLD = 10


def pool_average(rows: Iterable[Mapping[str, Any]]) -> float:
    """p0 — доля верных ответов по всей выборке (0..1). Пустая выборка → 0."""
    correct = 0
    total = 0
    for row in rows:
        correct += int(row.get("correct") or 0)
        total += int(row.get("total") or 0)
    if total <= 0:
        return 0.0
    return correct / total


def bayes_score(correct: int, total: int, *, p0: float, k: float = BAYES_K) -> float:
    """Сглаженная доля верных (0..1). При total = 0 возвращает p0."""
    if correct < 0 or total < 0 or correct > total:
        raise ValueError("Некорректные счётчики: требуется 0 <= correct <= total")
    if k < 0:
        raise ValueError("k не может быть отрицательным")
    denominator = total + k
    if denominator <= 0:
        return 0.0
    return (correct + k * p0) / denominator


def raw_percent(correct: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round(correct / total * 100, 1)


def build_leaderboard(
    rows: Iterable[Mapping[str, Any]],
    *,
    k: float = BAYES_K,
    low_data_threshold: int = LOW_DATA_THRESHOLD,
    limit: int | None = None,
) -> dict[str, Any]:
    """Рейтинг сотрудников.

    rows: {"operator_id", "operator_name", "correct", "total", "coverage"?}.
    Сотрудники с total = 0 исключаются (и не влияют на p0).
    Сортировка: score ↓, total ↓, имя ↑.
    """
    eligible = [dict(r) for r in rows if int(r.get("total") or 0) > 0]
    p0 = pool_average(eligible)

    items: list[dict[str, Any]] = []
    for row in eligible:
        correct = int(row.get("correct") or 0)
        total = int(row.get("total") or 0)
        score = bayes_score(correct, total, p0=p0, k=k)
        items.append(
            {
                "operator_id": int(row["operator_id"]),
                "operator_name": str(row.get("operator_name") or ""),
                "correct": correct,
                "total": total,
                "raw_percent": raw_percent(correct, total),
                "score": score,
                "score_percent": round(score * 100, 1),
                "coverage": int(row.get("coverage") or 0),
                "low_data": total < low_data_threshold,
            }
        )

    items.sort(key=lambda x: (-x["score"], -x["total"], x["operator_name"].lower()))
    for idx, item in enumerate(items, start=1):
        item["rank"] = idx

    if limit is not None:
        items = items[:limit]

    return {
        "k": k,
        "p0_percent": round(p0 * 100, 1),
        "low_data_threshold": low_data_threshold,
        "items": items,
    }
