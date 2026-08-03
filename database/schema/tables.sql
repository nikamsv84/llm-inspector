CREATE TABLE IF NOT EXISTS raw_requests (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method VARCHAR(10) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL,
    path TEXT NOT NULL,
    headers JSONB NOT NULL,
    raw_bytes BYTEA NOT NULL
);

CREATE TABLE IF NOT EXISTS intercept_queue (
    id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'forwarded', 'dropped')),
    CONSTRAINT fk_raw_request_queue FOREIGN KEY (request_id)
        REFERENCES raw_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS modified_requests (
    id BIGSERIAL PRIMARY KEY,
    request_id BIGINT NOT NULL UNIQUE,
    method VARCHAR(10) NOT NULL,
    path TEXT NOT NULL,
    headers JSONB NOT NULL,
    raw_bytes BYTEA NOT NULL,
    CONSTRAINT fk_raw_request_modified FOREIGN KEY (request_id)
        REFERENCES raw_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dashboard_status (
    id INT PRIMARY KEY DEFAULT 1,
    is_paused BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT single_row_check CHECK (id = 1)
);

INSERT INTO dashboard_status (id, is_paused)
VALUES (1, false)
ON CONFLICT (id) DO NOTHING;