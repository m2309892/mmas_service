"""A small logistic regression implementation for the churn prototype."""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Mapping

from .features import FEATURE_COLUMNS, TARGET_COLUMN, coerce_feature_row
from .synthetic_data import sigmoid


@dataclass
class LogisticChurnModel:
    feature_columns: list[str]
    weights: list[float]
    bias: float
    means: list[float]
    stds: list[float]
    threshold: float = 0.5
    metadata: dict[str, object] | None = None

    def _vectorize(self, row: Mapping[str, object]) -> list[float]:
        features = coerce_feature_row(row)
        values = [features[name] for name in self.feature_columns]
        return [
            (value - mean) / std if std else 0.0
            for value, mean, std in zip(values, self.means, self.stds)
        ]

    def predict_proba(self, row: Mapping[str, object]) -> float:
        vector = self._vectorize(row)
        score = self.bias + sum(weight * value for weight, value in zip(self.weights, vector))
        return sigmoid(score)

    def predict(self, row: Mapping[str, object]) -> dict[str, object]:
        probability = self.predict_proba(row)
        return {
            "churn_probability": round(probability, 6),
            "is_churned_predicted": probability >= self.threshold,
            "threshold": self.threshold,
        }

    def save(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(self)
        with path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def load(cls, path: str | Path) -> "LogisticChurnModel":
        with Path(path).open("r", encoding="utf-8") as file:
            payload = json.load(file)
        return cls(**payload)


def _as_matrix(rows: Iterable[Mapping[str, object]], feature_columns: list[str]) -> tuple[list[list[float]], list[int]]:
    matrix: list[list[float]] = []
    targets: list[int] = []
    for row in rows:
        features = coerce_feature_row(row)
        matrix.append([features[name] for name in feature_columns])
        targets.append(int(row[TARGET_COLUMN]))
    return matrix, targets


def _standardize(matrix: list[list[float]]) -> tuple[list[list[float]], list[float], list[float]]:
    columns = list(zip(*matrix))
    means = [sum(column) / len(column) for column in columns]
    stds = []
    for column, mean in zip(columns, means):
        variance = sum((value - mean) ** 2 for value in column) / len(column)
        stds.append(math.sqrt(variance) or 1.0)
    scaled = [
        [(value - mean) / std for value, mean, std in zip(row, means, stds)]
        for row in matrix
    ]
    return scaled, means, stds


def train_logistic_model(
    rows: list[Mapping[str, object]],
    *,
    feature_columns: list[str] | None = None,
    epochs: int = 900,
    learning_rate: float = 0.05,
    l2: float = 0.001,
    threshold: float = 0.5,
) -> LogisticChurnModel:
    feature_columns = feature_columns or list(FEATURE_COLUMNS)
    matrix, targets = _as_matrix(rows, feature_columns)
    scaled, means, stds = _standardize(matrix)

    weights = [0.0 for _ in feature_columns]
    bias = 0.0
    n_rows = len(scaled)

    for _ in range(epochs):
        grad_weights = [0.0 for _ in feature_columns]
        grad_bias = 0.0
        for vector, target in zip(scaled, targets):
            score = bias + sum(weight * value for weight, value in zip(weights, vector))
            error = sigmoid(score) - target
            grad_bias += error
            for index, value in enumerate(vector):
                grad_weights[index] += error * value

        bias -= learning_rate * (grad_bias / n_rows)
        for index, weight in enumerate(weights):
            regularized_grad = grad_weights[index] / n_rows + l2 * weight
            weights[index] -= learning_rate * regularized_grad

    return LogisticChurnModel(
        feature_columns=feature_columns,
        weights=weights,
        bias=bias,
        means=means,
        stds=stds,
        threshold=threshold,
        metadata={
            "model_type": "stdlib_logistic_regression",
            "epochs": epochs,
            "learning_rate": learning_rate,
            "l2": l2,
            "training_rows": len(rows),
        },
    )


def split_train_test(
    rows: list[Mapping[str, object]],
    *,
    test_size: float = 0.2,
    seed: int = 42,
) -> tuple[list[Mapping[str, object]], list[Mapping[str, object]]]:
    shuffled = list(rows)
    random.Random(seed).shuffle(shuffled)
    split_at = max(1, int(len(shuffled) * (1 - test_size)))
    return shuffled[:split_at], shuffled[split_at:]


def evaluate(model: LogisticChurnModel, rows: Iterable[Mapping[str, object]]) -> dict[str, float | int]:
    tp = fp = tn = fn = 0
    log_loss = 0.0
    count = 0
    for row in rows:
        target = int(row[TARGET_COLUMN])
        probability = min(max(model.predict_proba(row), 1e-9), 1 - 1e-9)
        predicted = probability >= model.threshold
        if target == 1 and predicted:
            tp += 1
        elif target == 0 and predicted:
            fp += 1
        elif target == 0 and not predicted:
            tn += 1
        else:
            fn += 1
        log_loss += -(target * math.log(probability) + (1 - target) * math.log(1 - probability))
        count += 1

    accuracy = (tp + tn) / count if count else 0.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "rows": count,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "log_loss": round(log_loss / count, 4) if count else 0.0,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }
