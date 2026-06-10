"""Run local inference with a saved churn model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .logistic_model import LogisticChurnModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Predict MMAS churn risk")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True, help="JSON with feature columns")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = LogisticChurnModel.load(args.model)
    with args.input.open("r", encoding="utf-8") as file:
        row = json.load(file)
    prediction = model.predict(row)
    print(json.dumps(prediction, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
