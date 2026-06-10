"""Synthetic dataset generator for churn experiments."""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

from .features import FEATURE_COLUMNS, TARGET_COLUMN


@dataclass(frozen=True)
class SyntheticConfig:
    rows: int = 2500
    seed: int = 42
    snapshot_date: date = date(2026, 1, 1)


def sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


def _bounded_gauss(rng: random.Random, mean: float, std: float, low: int, high: int) -> int:
    return max(low, min(high, int(round(rng.gauss(mean, std)))))


def _make_row(index: int, rng: random.Random, snapshot_date: date) -> dict[str, object]:
    age_years = _bounded_gauss(rng, 18, 9, 5, 58)
    is_child = 1 if age_years < 16 else 0

    engagement = rng.betavariate(2.2, 2.4)
    tenure_days = _bounded_gauss(rng, 360 + engagement * 900, 210, 7, 2400)
    visits_30d = max(0, _bounded_gauss(rng, 1 + engagement * 8, 2.0, 0, 22))
    visits_60d = visits_30d + max(0, _bounded_gauss(rng, engagement * 7, 2.5, 0, 24))
    visits_90d = visits_60d + max(0, _bounded_gauss(rng, engagement * 7, 3.0, 0, 30))

    if visits_30d > 0:
        days_since_last_visit = _bounded_gauss(rng, 4 + (1 - engagement) * 12, 5, 0, 35)
    else:
        days_since_last_visit = _bounded_gauss(rng, 28 + (1 - engagement) * 55, 18, 10, 140)

    unpaid_count_90d = max(0, _bounded_gauss(rng, (1 - engagement) * 3, 1.4, 0, 12))
    paid_ratio_90d = max(0.0, min(1.0, rng.gauss(0.88 - unpaid_count_90d * 0.08, 0.12)))

    has_active_aboniment = rng.random() < 0.35 + engagement * 0.45
    active_aboniment_days_left = (
        _bounded_gauss(rng, 20 + engagement * 35, 15, 0, 120) if has_active_aboniment else 0
    )
    active_aboniment_hours_left = (
        _bounded_gauss(rng, 4 + engagement * 18, 5, 0, 80) if has_active_aboniment else 0
    )

    purchases_90d = max(0, _bounded_gauss(rng, engagement * 2.5, 1.0, 0, 8))
    balance = round(rng.gauss(1200 * engagement - 400 * unpaid_count_90d, 1600), 2)
    avg_gap_days = round(90 / max(visits_90d, 1), 2)
    belt_sort_order = _bounded_gauss(rng, 1 + tenure_days / 240, 1.5, 1, 12)
    studio_students_count = _bounded_gauss(rng, 85, 35, 15, 220)

    logit = (
        -2.8
        + 0.055 * days_since_last_visit
        - 0.22 * visits_30d
        - 0.05 * visits_60d
        + 0.28 * unpaid_count_90d
        - 1.15 * paid_ratio_90d
        - 0.018 * active_aboniment_days_left
        - 0.035 * active_aboniment_hours_left
        - 0.34 * purchases_90d
        + 0.018 * avg_gap_days
        - 0.0007 * tenure_days
        - 0.045 * belt_sort_order
        + (0.28 if balance < -500 else 0)
        + (0.18 if is_child else 0)
    )
    churn_probability = sigmoid(logit)
    is_churned = 1 if rng.random() < churn_probability else 0

    row: dict[str, object] = {
        "mmas_id": f"SYN-{index + 1:05d}",
        "snapshot_date": snapshot_date.isoformat(),
        "churn_probability_hidden": round(churn_probability, 4),
        TARGET_COLUMN: is_churned,
        "age_years": age_years,
        "tenure_days": tenure_days,
        "balance": balance,
        "visits_30d": visits_30d,
        "visits_60d": visits_60d,
        "visits_90d": visits_90d,
        "days_since_last_visit": days_since_last_visit,
        "unpaid_count_90d": unpaid_count_90d,
        "paid_ratio_90d": round(paid_ratio_90d, 4),
        "active_aboniment_days_left": active_aboniment_days_left,
        "active_aboniment_hours_left": active_aboniment_hours_left,
        "purchases_90d": purchases_90d,
        "avg_gap_days": avg_gap_days,
        "belt_sort_order": belt_sort_order,
        "studio_students_count": studio_students_count,
        "is_child": is_child,
    }
    return row


def generate_rows(config: SyntheticConfig) -> list[dict[str, object]]:
    rng = random.Random(config.seed)
    return [_make_row(index, rng, config.snapshot_date) for index in range(config.rows)]


def write_csv(path: str | Path, rows: Iterable[dict[str, object]]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    fieldnames = ["mmas_id", "snapshot_date", *FEATURE_COLUMNS, TARGET_COLUMN, "churn_probability_hidden"]
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str | Path) -> list[dict[str, object]]:
    with Path(path).open("r", newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))
