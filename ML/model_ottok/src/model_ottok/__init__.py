"""Customer churn prototype for MMAS."""

from .features import FEATURE_COLUMNS, TARGET_COLUMN
from .logistic_model import LogisticChurnModel

__all__ = ["FEATURE_COLUMNS", "TARGET_COLUMN", "LogisticChurnModel"]
