"""Feature contract for the churn model.

The names are intentionally close to the current MMAS domain models:
students, attendance, aboniments, balance logs, belts and studios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


TARGET_COLUMN = "is_churned"

FEATURE_COLUMNS = [
    "age_years",
    "tenure_days",
    "balance",
    "visits_30d",
    "visits_60d",
    "visits_90d",
    "days_since_last_visit",
    "unpaid_count_90d",
    "paid_ratio_90d",
    "active_aboniment_days_left",
    "active_aboniment_hours_left",
    "purchases_90d",
    "avg_gap_days",
    "belt_sort_order",
    "studio_students_count",
    "is_child",
]


@dataclass(frozen=True)
class FeatureValidationResult:
    ok: bool
    missing: list[str]
    non_numeric: list[str]


def validate_feature_row(row: Mapping[str, object]) -> FeatureValidationResult:
    missing = [name for name in FEATURE_COLUMNS if name not in row]
    non_numeric: list[str] = []
    for name in FEATURE_COLUMNS:
        if name not in row:
            continue
        try:
            float(row[name])
        except (TypeError, ValueError):
            non_numeric.append(name)
    return FeatureValidationResult(
        ok=not missing and not non_numeric,
        missing=missing,
        non_numeric=non_numeric,
    )


def coerce_feature_row(row: Mapping[str, object]) -> dict[str, float]:
    validation = validate_feature_row(row)
    if not validation.ok:
        details = []
        if validation.missing:
            details.append(f"missing={validation.missing}")
        if validation.non_numeric:
            details.append(f"non_numeric={validation.non_numeric}")
        raise ValueError("Invalid churn feature row: " + ", ".join(details))
    return {name: float(row[name]) for name in FEATURE_COLUMNS}
