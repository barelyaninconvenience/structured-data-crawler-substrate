-- Structured Data Crawler Substrate — SQLite schema (v1 6-dimension rubric)
-- 2026-04-24

CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,      -- 'remoteok', 'wwr', 'remotive', etc.
    display_name TEXT NOT NULL,
    auth_required INTEGER NOT NULL,  -- 0 or 1
    crawler_type TEXT NOT NULL,      -- 'api', 'rss', 'crawl4ai', 'playwright'
    notes TEXT
);

INSERT OR IGNORE INTO sources VALUES
    ('remoteok', 'RemoteOK', 0, 'api', 'Public JSON API at remoteok.com/api'),
    ('remotive', 'Remotive', 0, 'api', 'Public REST API at remotive.com/api/remote-jobs'),
    ('jobicy', 'Jobicy', 0, 'api', 'Public REST API at jobicy.com/api/v2/remote-jobs'),
    ('working_nomads', 'Working Nomads', 0, 'api', 'Public JSON + RSS fallback'),
    ('remote_co', 'Remote.co', 0, 'rss', 'Per-category RSS feeds'),
    ('skipthedrive', 'SkipTheDrive', 0, 'rss', 'Per-category RSS feeds'),
    ('wwr', 'We Work Remotely', 0, 'rss', 'Per-category RSS feeds'),
    ('indeed', 'Indeed', 0, 'crawl4ai', 'Public search via crawl4ai'),
    ('wellfound', 'Wellfound', 0, 'crawl4ai', 'Startup-focused; public search'),
    ('ziprecruiter', 'ZipRecruiter', 0, 'crawl4ai', 'Public search'),
    ('crawl4ai_generic', 'Generic Crawl4AI Fallback', 0, 'crawl4ai', 'Any-site fallback'),
    ('kaggle_dataset', 'Kaggle Dataset Ingest', 0, 'kaggle', 'Offline corpus ingestion');

CREATE TABLE IF NOT EXISTS raw_jobs (
    id TEXT PRIMARY KEY,             -- SHA256 hash of (source_url + title + company)[:16]
    source TEXT NOT NULL REFERENCES sources(source_id),
    source_url TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT,
    pay_raw TEXT,
    pay_min INTEGER,
    pay_max INTEGER,
    pay_type TEXT,                   -- 'hourly', 'annual', 'unknown'
    remote_status TEXT,              -- 'fully_remote', 'hybrid', 'onsite', 'unclear'
    location TEXT,
    description_md TEXT,
    posted_date TEXT,                -- ISO 8601 from source
    scraped_at TEXT NOT NULL,        -- ISO 8601 UTC of when we fetched
    raw_html_path TEXT,              -- optional: path to raw cached HTML
    dedup_group_id TEXT              -- set after dedup pass
);

CREATE INDEX IF NOT EXISTS idx_raw_jobs_source ON raw_jobs(source);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_scraped_at ON raw_jobs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_raw_jobs_dedup ON raw_jobs(dedup_group_id);

CREATE TABLE IF NOT EXISTS scored_jobs (
    id TEXT PRIMARY KEY REFERENCES raw_jobs(id),
    score_automatability INTEGER,
    score_oversight INTEGER,
    score_pay INTEGER,
    score_remote INTEGER,
    score_stakes INTEGER,
    score_flexibility INTEGER,
    score_total INTEGER,
    red_flags TEXT,                  -- JSON array
    green_flags TEXT,                -- JSON array
    verdict TEXT,
    recommend TEXT,                  -- 'apply', 'maybe', 'skip'
    scored_at TEXT NOT NULL,
    model_used TEXT
);

CREATE INDEX IF NOT EXISTS idx_scored_jobs_total ON scored_jobs(score_total);
CREATE INDEX IF NOT EXISTS idx_scored_jobs_recommend ON scored_jobs(recommend);

CREATE TABLE IF NOT EXISTS applications (
    job_id TEXT PRIMARY KEY REFERENCES raw_jobs(id),
    status TEXT NOT NULL,            -- 'queued', 'applied', 'interview', 'rejected', 'offer', 'declined', 'accepted'
    applied_at TEXT,
    notes TEXT,
    cover_letter_path TEXT
);

CREATE VIEW IF NOT EXISTS v_shortlist AS
SELECT
    r.id, r.source, r.title, r.company, r.pay_raw, r.pay_min, r.pay_max,
    r.remote_status,
    s.score_total, s.recommend, s.verdict, s.red_flags, s.green_flags,
    COALESCE(a.status, 'not_applied') as application_status
FROM raw_jobs r
JOIN scored_jobs s ON s.id = r.id
LEFT JOIN applications a ON a.job_id = r.id
WHERE s.recommend IN ('apply', 'maybe')
ORDER BY s.score_total DESC, r.scraped_at DESC;
