CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE SCHEMA IF NOT EXISTS audit;
CREATE TABLE IF NOT EXISTS audit.pipeline_runs (
    pipeline_run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    pipeline_name VARCHAR(255) NOT NULL,
    source_name VARCHAR(255),
    status VARCHAR(50) NOT NULL,

    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,

    extracted_rows BIGINT DEFAULT 0,
    inserted_rows BIGINT DEFAULT 0,
    updated_rows BIGINT DEFAULT 0,
    rejected_rows BIGINT DEFAULT 0,

    error_message TEXT
);