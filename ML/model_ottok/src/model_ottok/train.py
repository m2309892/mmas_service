"""Train the churn prototype on synthetic data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .logistic_model import evaluate, split_train_test, train_logistic_model
from .synthetic_data import SyntheticConfig, generate_rows, write_csv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train synthetic MMAS churn model")
    parser.add_argument("--rows", type=int, default=2500)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=900)
    parser.add_argument("--learning-rate", type=float, default=0.05)
    parser.add_argument("--l2", type=float, default=0.001)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--dataset-out", type=Path, default=Path("artifacts/synthetic_churn.csv"))
    parser.add_argument("--model-out", type=Path, default=Path("artifacts/churn_model.json"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = generate_rows(SyntheticConfig(rows=args.rows, seed=args.seed))
    write_csv(args.dataset_out, rows)

    train_rows, test_rows = split_train_test(rows, seed=args.seed)
    model = train_logistic_model(
        train_rows,
        epochs=args.epochs,
        learning_rate=args.learning_rate,
        l2=args.l2,
        threshold=args.threshold,
    )
    metrics = evaluate(model, test_rows)
    model.metadata = {
        **(model.metadata or {}),
        "dataset_out": str(args.dataset_out),
        "test_metrics": metrics,
    }
    model.save(args.model_out)

    print(
        json.dumps(
            {
                "dataset": str(args.dataset_out),
                "model": str(args.model_out),
                "metrics": metrics,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
