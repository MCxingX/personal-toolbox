from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCHEMA_VERSION = 2


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            self._migrate(conn)
            current = conn.execute("SELECT value FROM app_meta WHERE key='schema_version'").fetchone()
            if current is None:
                conn.execute("INSERT INTO app_meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))

    def _migrate(self, conn: sqlite3.Connection) -> None:
        def columns(table: str) -> set[str]:
            return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}

        weather_cols = columns("weather_forecasts")
        if "weathercode" not in weather_cols:
            conn.execute("ALTER TABLE weather_forecasts ADD COLUMN weathercode INTEGER DEFAULT 0")
        if "humidity" not in weather_cols:
            conn.execute("ALTER TABLE weather_forecasts ADD COLUMN humidity TEXT DEFAULT ''")
        if "wind_speed" not in weather_cols:
            conn.execute("ALTER TABLE weather_forecasts ADD COLUMN wind_speed TEXT DEFAULT ''")
        if "feels_like" not in weather_cols:
            conn.execute("ALTER TABLE weather_forecasts ADD COLUMN feels_like TEXT DEFAULT ''")
        if "uv_index" not in weather_cols:
            conn.execute("ALTER TABLE weather_forecasts ADD COLUMN uv_index TEXT DEFAULT ''")

        api_cols = columns("api_catalog")
        if "api_kind" not in api_cols:
            conn.execute("ALTER TABLE api_catalog ADD COLUMN api_kind TEXT NOT NULL DEFAULT 'built_in'")
        if "api_key" not in api_cols:
            conn.execute("ALTER TABLE api_catalog ADD COLUMN api_key TEXT NOT NULL DEFAULT ''")
        if "target_module" not in api_cols:
            conn.execute("ALTER TABLE api_catalog ADD COLUMN target_module TEXT NOT NULL DEFAULT ''")

        quote_cols = columns("daily_quotes")
        if "lesson" not in quote_cols:
            conn.execute("ALTER TABLE daily_quotes ADD COLUMN lesson TEXT NOT NULL DEFAULT ''")
        if "action" not in quote_cols:
            conn.execute("ALTER TABLE daily_quotes ADD COLUMN action TEXT NOT NULL DEFAULT ''")
        if "shown_count" not in quote_cols:
            conn.execute("ALTER TABLE daily_quotes ADD COLUMN shown_count INTEGER NOT NULL DEFAULT 0")
        if "last_shown_at" not in quote_cols:
            conn.execute("ALTER TABLE daily_quotes ADD COLUMN last_shown_at TEXT")


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS app_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE IF NOT EXISTS source_configs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    url TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    rate_limit_per_minute INTEGER NOT NULL DEFAULT 6,
    auth_type TEXT NOT NULL DEFAULT 'none',
    auth_config TEXT NOT NULL DEFAULT '{}',
    parse_rules TEXT NOT NULL DEFAULT '{}',
    last_success_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS articles(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    url TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'news',
    tags TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    credibility_score REAL NOT NULL DEFAULT 0.6,
    importance_score REAL NOT NULL DEFAULT 0.5,
    region TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL DEFAULT '',
    language TEXT NOT NULL DEFAULT 'zh',
    sentiment TEXT NOT NULL DEFAULT 'neutral',
    duplicate_of INTEGER,
    UNIQUE(url)
);

CREATE TABLE IF NOT EXISTS earthquake_events(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    magnitude REAL NOT NULL,
    latitude REAL,
    longitude REAL,
    depth_km REAL,
    place TEXT NOT NULL,
    event_time TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'usgs',
    detail_url TEXT,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weather_forecasts(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    latitude REAL,
    longitude REAL,
    forecast_date TEXT NOT NULL,
    temp_high REAL,
    temp_low REAL,
    description TEXT NOT NULL DEFAULT '',
    weathercode INTEGER DEFAULT 0,
    raw_json TEXT NOT NULL DEFAULT '{}',
    source TEXT NOT NULL DEFAULT 'open-meteo',
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS keyword_queries(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'local',
    result_count INTEGER NOT NULL DEFAULT 0,
    searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS hot_reports(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    time_window TEXT NOT NULL,
    topics_json TEXT NOT NULL DEFAULT '[]',
    summary TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    item_type,
    item_id UNINDEXED,
    title,
    body,
    tags,
    source
);

CREATE TABLE IF NOT EXISTS reading_states(
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'unread',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(item_type, item_id)
);

CREATE TABLE IF NOT EXISTS collections(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    collection_type TEXT NOT NULL,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(item_type, item_id, collection_type)
);

CREATE TABLE IF NOT EXISTS special_favorite_sources(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    entry_url TEXT NOT NULL,
    match_domain TEXT NOT NULL,
    match_path TEXT NOT NULL DEFAULT '',
    match_mode TEXT NOT NULL DEFAULT 'domain',
    category TEXT NOT NULL DEFAULT 'custom',
    parse_rule TEXT NOT NULL DEFAULT '',
    enabled INTEGER NOT NULL DEFAULT 1,
    tab_order INTEGER NOT NULL DEFAULT 0,
    icon TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS special_favorite_matches(
    favorite_id INTEGER NOT NULL REFERENCES special_favorite_sources(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    matched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(favorite_id, article_id)
);

CREATE TABLE IF NOT EXISTS watchlist_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    keywords TEXT NOT NULL,
    exclude_words TEXT NOT NULL DEFAULT '',
    priority INTEGER NOT NULL DEFAULT 5,
    enabled INTEGER NOT NULL DEFAULT 1,
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_briefs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brief_type TEXT NOT NULL,
    brief_date TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    missing_sources TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(brief_type, brief_date)
);

CREATE TABLE IF NOT EXISTS export_jobs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_type TEXT NOT NULL,
    item_id INTEGER,
    format TEXT NOT NULL,
    output_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backup_records(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'success',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS credibility_explanations(
    item_type TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    score REAL NOT NULL,
    explanation TEXT NOT NULL,
    factors TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(item_type, item_id)
);

CREATE TABLE IF NOT EXISTS source_health_metrics(
    source_id INTEGER PRIMARY KEY REFERENCES source_configs(id) ON DELETE CASCADE,
    success_count INTEGER NOT NULL DEFAULT 0,
    failure_count INTEGER NOT NULL DEFAULT 0,
    avg_response_ms REAL NOT NULL DEFAULT 0,
    last_success_at TEXT,
    last_error TEXT,
    paused INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_queue(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS privacy_mode_state(
    id INTEGER PRIMARY KEY CHECK(id = 1),
    enabled INTEGER NOT NULL DEFAULT 0,
    previous_source_state TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_prefs(
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL DEFAULT '',
    item_type TEXT NOT NULL DEFAULT '',
    item_id INTEGER,
    status TEXT NOT NULL DEFAULT 'unread',
    priority INTEGER NOT NULL DEFAULT 5,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscription_rules(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    keywords TEXT NOT NULL DEFAULT '[]',
    categories TEXT NOT NULL DEFAULT '[]',
    regions TEXT NOT NULL DEFAULT '[]',
    sources TEXT NOT NULL DEFAULT '[]',
    min_hotness REAL NOT NULL DEFAULT 0,
    min_credibility REAL NOT NULL DEFAULT 0,
    frequency TEXT NOT NULL DEFAULT 'instant',
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_catalog(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    auth_type TEXT NOT NULL DEFAULT 'No',
    https INTEGER NOT NULL DEFAULT 1,
    cors TEXT NOT NULL DEFAULT 'unknown',
    docs_url TEXT NOT NULL DEFAULT '',
    base_url TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'disabled',
    risk_tags TEXT NOT NULL DEFAULT '',
    default_rate_limit INTEGER NOT NULL DEFAULT 60,
    output_type TEXT NOT NULL DEFAULT 'json',
    api_kind TEXT NOT NULL DEFAULT 'built_in',
    api_key TEXT NOT NULL DEFAULT '',
    target_module TEXT NOT NULL DEFAULT '',
    params_schema TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_call_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_id INTEGER REFERENCES api_catalog(id) ON DELETE SET NULL,
    endpoint TEXT NOT NULL,
    params TEXT NOT NULL DEFAULT '{}',
    status_code INTEGER,
    response_size INTEGER NOT NULL DEFAULT 0,
    response_time_ms REAL NOT NULL DEFAULT 0,
    success INTEGER NOT NULL DEFAULT 0,
    error TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_quotes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL DEFAULT 'local',
    style TEXT NOT NULL DEFAULT 'encourage',
    lesson TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL DEFAULT '',
    shown_count INTEGER NOT NULL DEFAULT 0,
    last_shown_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tech_changes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    channel TEXT NOT NULL DEFAULT '',
    impact TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL DEFAULT '',
    change_type TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    importance REAL NOT NULL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS captured_exchanges(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    import_batch TEXT NOT NULL,
    url TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'GET',
    status_code INTEGER,
    mime_type TEXT NOT NULL DEFAULT '',
    response_time_ms REAL,
    response_size INTEGER,
    request_headers TEXT NOT NULL DEFAULT '{}',
    response_body TEXT NOT NULL DEFAULT '',
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS import_candidates(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exchange_id INTEGER REFERENCES captured_exchanges(id) ON DELETE CASCADE,
    candidate_type TEXT NOT NULL,
    title TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS policy_items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    issuer TEXT NOT NULL DEFAULT '',
    document_no TEXT NOT NULL DEFAULT '',
    published_at TEXT,
    effective_at TEXT,
    region TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT '',
    summary TEXT NOT NULL DEFAULT '',
    source_url TEXT NOT NULL DEFAULT '',
    source_name TEXT NOT NULL DEFAULT '',
    collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS web_page_sources(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    url_pattern TEXT NOT NULL DEFAULT '',
    title_selector TEXT NOT NULL DEFAULT '',
    link_selector TEXT NOT NULL DEFAULT 'a[href]',
    summary_selector TEXT NOT NULL DEFAULT '',
    content_selector TEXT NOT NULL DEFAULT '',
    date_selector TEXT NOT NULL DEFAULT '',
    author_selector TEXT NOT NULL DEFAULT '',
    item_selector TEXT NOT NULL DEFAULT '',
    use_xpath INTEGER NOT NULL DEFAULT 0,
    encoding TEXT NOT NULL DEFAULT '',
    max_items INTEGER NOT NULL DEFAULT 30,
    remove_selectors TEXT NOT NULL DEFAULT '[]',
    category TEXT NOT NULL DEFAULT 'web',
    enabled INTEGER NOT NULL DEFAULT 1,
    last_fetch_at TEXT,
    last_error TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""
