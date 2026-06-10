-- Draft only. Convert to Alembic migration after the feature contract is approved.

CREATE TABLE IF NOT EXISTS ml_churn_feature_snapshots (
    id BIGSERIAL PRIMARY KEY,
    mmas_id_hash VARCHAR(64) NOT NULL,
    snapshot_date DATE NOT NULL,
    source_version VARCHAR(100) NOT NULL,
    feature_payload JSONB NOT NULL,
    target_is_churned BOOLEAN NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (mmas_id_hash, snapshot_date, source_version)
);

CREATE INDEX IF NOT EXISTS ix_ml_churn_snapshots_date
    ON ml_churn_feature_snapshots (snapshot_date);

CREATE TABLE IF NOT EXISTS ml_churn_predictions (
    id BIGSERIAL PRIMARY KEY,
    mmas_id_hash VARCHAR(64) NOT NULL,
    snapshot_date DATE NOT NULL,
    model_version VARCHAR(100) NOT NULL,
    features_version VARCHAR(100) NOT NULL,
    churn_probability NUMERIC(8, 6) NOT NULL,
    threshold NUMERIC(8, 6) NOT NULL,
    prediction_payload JSONB NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_ml_churn_predictions_lookup
    ON ml_churn_predictions (mmas_id_hash, snapshot_date, model_version);
