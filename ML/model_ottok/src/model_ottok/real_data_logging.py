"""Draft logging helpers for real churn features and predictions.

These helpers avoid importing the production app directly. The backend can call
them from a job or API adapter after it computes features from SQLAlchemy rows.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Mapping

from .features import FEATURE_COLUMNS, coerce_feature_row


@dataclass(frozen=True)
class FeatureSnapshot:
    mmas_id_hash: str
    snapshot_date: str
    features: dict[str, float]
    source_version: str = "churn_features_v0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class PredictionLog:
    mmas_id_hash: str
    snapshot_date: str
    model_version: str
    churn_probability: float
    threshold: float
    features_version: str = "churn_features_v0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def hash_mmas_id(mmas_id: str, *, salt: str) -> str:
    if not salt:
        raise ValueError("salt must be set before logging real identifiers")
    return hashlib.sha256(f"{salt}:{mmas_id}".encode("utf-8")).hexdigest()


def build_feature_snapshot(
    *,
    mmas_id: str,
    salt: str,
    snapshot_date: date,
    raw_features: Mapping[str, object],
    source_version: str = "churn_features_v0",
) -> FeatureSnapshot:
    return FeatureSnapshot(
        mmas_id_hash=hash_mmas_id(mmas_id, salt=salt),
        snapshot_date=snapshot_date.isoformat(),
        features=coerce_feature_row(raw_features),
        source_version=source_version,
    )


class JsonlLogger:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, payload: Mapping[str, object]) -> None:
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")

    def append_dataclass(self, payload: object) -> None:
        self.append(asdict(payload))


def build_prediction_log(
    *,
    mmas_id: str,
    salt: str,
    snapshot_date: date,
    model_version: str,
    churn_probability: float,
    threshold: float,
    features_version: str = "churn_features_v0",
) -> PredictionLog:
    return PredictionLog(
        mmas_id_hash=hash_mmas_id(mmas_id, salt=salt),
        snapshot_date=snapshot_date.isoformat(),
        model_version=model_version,
        churn_probability=round(float(churn_probability), 6),
        threshold=float(threshold),
        features_version=features_version,
    )


def expected_feature_payload() -> dict[str, str]:
    return {name: "float" for name in FEATURE_COLUMNS}
