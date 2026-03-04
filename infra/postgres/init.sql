-- ============================================================
-- Forensic System — PostgreSQL Initialization
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enum Types ────────────────────────────────────────────────────────────────
CREATE TYPE user_role        AS ENUM ('analyst', 'admin', 'viewer');
CREATE TYPE evidence_status  AS ENUM ('pending', 'processing', 'completed', 'failed');
CREATE TYPE media_type       AS ENUM ('image', 'video');
CREATE TYPE audit_event_type AS ENUM (
    'login', 'logout', 'upload', 'analysis_start',
    'analysis_complete', 'download', 'admin_action', 'auth_failure'
);

-- ── Users ─────────────────────────────────────────────────────────────────────
CREATE TABLE users (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    role          user_role   NOT NULL DEFAULT 'analyst',
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login    TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);

-- ── Model Versions ────────────────────────────────────────────────────────────
CREATE TABLE model_versions (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    model_name       VARCHAR(100) NOT NULL,
    version_tag      VARCHAR(50)  NOT NULL,
    architecture     VARCHAR(100) NOT NULL,
    dataset_trained  VARCHAR(200),
    accuracy         FLOAT,
    f1_score         FLOAT,
    sha256_checksum  CHAR(64),
    is_active        BOOLEAN     NOT NULL DEFAULT TRUE,
    registered_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (model_name, version_tag)
);

-- ── Evidence ──────────────────────────────────────────────────────────────────
CREATE TABLE evidence (
    id           UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    uploaded_by  UUID           NOT NULL REFERENCES users(id),
    filename     VARCHAR(255)   NOT NULL,
    storage_key  VARCHAR(512)   NOT NULL UNIQUE,  -- UUID path in MinIO
    file_size    BIGINT         NOT NULL,
    mime_type    VARCHAR(100)   NOT NULL,
    sha256_hash  CHAR(64)       NOT NULL,
    media_type   media_type     NOT NULL,
    status       evidence_status NOT NULL DEFAULT 'pending',
    uploaded_at  TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    ip_address   INET           NOT NULL,
    is_deleted   BOOLEAN        NOT NULL DEFAULT FALSE  -- soft delete
);

CREATE INDEX idx_evidence_uploaded_by ON evidence(uploaded_by);
CREATE INDEX idx_evidence_status      ON evidence(status);
CREATE INDEX idx_evidence_sha256      ON evidence(sha256_hash);

-- ── Analysis Results ──────────────────────────────────────────────────────────
CREATE TABLE analysis_results (
    id                UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id       UUID    NOT NULL REFERENCES evidence(id),
    model_version_id  UUID    NOT NULL REFERENCES model_versions(id),
    celery_task_id    VARCHAR(255),
    is_tampered       BOOLEAN,
    confidence_score  FLOAT,
    processing_time_s FLOAT,
    ela_heatmap_key   VARCHAR(512),  -- MinIO object key for ELA output
    frame_results     JSONB,         -- [{frame_no, is_tampered, confidence}]
    metadata          JSONB,         -- Additional forensic notes
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_results_evidence_id ON analysis_results(evidence_id);
CREATE INDEX idx_results_model_id    ON analysis_results(model_version_id);

-- ── Audit Logs (append-only) ──────────────────────────────────────────────────
CREATE TABLE audit_logs (
    id          UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID           REFERENCES users(id),
    event_type  audit_event_type NOT NULL,
    resource_id UUID,           -- FK to evidence or analysis_results
    ip_address  INET,
    user_agent  TEXT,
    details     JSONB,
    occurred_at TIMESTAMPTZ    NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user_id    ON audit_logs(user_id);
CREATE INDEX idx_audit_event_type ON audit_logs(event_type);
CREATE INDEX idx_audit_occurred   ON audit_logs(occurred_at DESC);

-- !! CRITICAL: Revoke mutating permissions on audit_logs from app role
-- (Run after creating the app DB user)
-- REVOKE UPDATE, DELETE ON audit_logs FROM forensics_user;

-- ── Seed: Default Admin Account ───────────────────────────────────────────────
-- Password: Admin@Forensics123! (bcrypt hash — CHANGE IN PRODUCTION)
INSERT INTO users (email, full_name, role, password_hash)
VALUES (
    'admin@forensics.local',
    'System Administrator',
    'admin',
    '$2b$12$placeholder_bcrypt_hash_replace_before_deploy'
);

-- ── Seed: Default Model Version ───────────────────────────────────────────────
INSERT INTO model_versions (model_name, version_tag, architecture, dataset_trained)
VALUES
    ('xception_forensic', 'v1.0.0', 'XceptionNet', 'FaceForensics++'),
    ('cnn_lstm_video',    'v1.0.0', 'CNN+LSTM',    'FaceForensics++ video');
