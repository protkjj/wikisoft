"""
SQLite Database Manager

서버 재시작해도 데이터가 유지되는 영속 저장소.
JSON 파일 기반 → SQLite 통합.
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Optional
from contextlib import contextmanager

# DB 파일 경로
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DB_DIR / "wikisoft4.db"

# 싱글톤 커넥션
_connection: Optional[sqlite3.Connection] = None


def get_db() -> sqlite3.Connection:
    """SQLite 커넥션 반환 (싱글톤)."""
    global _connection
    if _connection is None:
        DB_DIR.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
    return _connection


@contextmanager
def get_cursor():
    """트랜잭션 자동 관리 커서."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def init_db() -> None:
    """테이블 생성 (앱 시작 시 호출)."""
    conn = get_db()

    conn.executescript("""
        -- 1. 검증 이력
        CREATE TABLE IF NOT EXISTS validation_history (
            id TEXT PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            filename TEXT,
            company_name TEXT,
            status TEXT,
            action TEXT,
            confidence REAL,
            message TEXT,
            error_count INTEGER,
            warning_count INTEGER,
            row_count INTEGER,
            user_id TEXT,
            session_id TEXT,
            run_id TEXT,
            details TEXT  -- JSON
        );

        -- 2. 매칭 케이스 (Few-shot 학습)
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE,
            timestamp DATETIME,
            confidence REAL,
            was_auto_approved BOOLEAN,
            headers TEXT,       -- JSON array
            normalized_headers TEXT,  -- JSON array
            matches TEXT,       -- JSON array
            human_corrections TEXT,  -- JSON
            metadata TEXT       -- JSON
        );

        -- 3. 시스템 설정
        CREATE TABLE IF NOT EXISTS system_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- 4. 에러 규칙 (학습)
        CREATE TABLE IF NOT EXISTS error_rules (
            id TEXT PRIMARY KEY,
            category TEXT,
            field TEXT,
            condition TEXT,
            severity TEXT,
            message TEXT,
            context_override TEXT,  -- JSON
            learned_at DATETIME,
            source TEXT
        );

        -- 5. 학습된 패턴 (사용자 피드백)
        CREATE TABLE IF NOT EXISTS learned_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            field TEXT,
            original_value TEXT,
            ai_said_error BOOLEAN,
            correct_interpretation TEXT,
            context TEXT,  -- JSON
            learned_at DATETIME
        );

        -- 6. 행동 로그 (자율학습)
        CREATE TABLE IF NOT EXISTS behavior_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            context TEXT,  -- JSON
            session_id TEXT,
            analyzed BOOLEAN DEFAULT 0
        );

        -- 인덱스
        CREATE INDEX IF NOT EXISTS idx_vh_timestamp ON validation_history(timestamp);
        CREATE INDEX IF NOT EXISTS idx_vh_user_id ON validation_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_cases_case_id ON cases(case_id);
        CREATE INDEX IF NOT EXISTS idx_be_analyzed ON behavior_events(analyzed);
        CREATE INDEX IF NOT EXISTS idx_er_category ON error_rules(category);
    """)

    print("  DB initialized:", DB_PATH)


def migrate_json_to_sqlite() -> dict:
    """기존 JSON 데이터를 SQLite로 마이그레이션."""
    base_dir = Path(__file__).parent.parent
    stats = {"validation_history": 0, "cases": 0, "settings": 0, "error_rules": 0, "behavior_events": 0}

    # 1. validation_history.json
    vh_path = base_dir / "training_data" / "validation_history.json"
    if vh_path.exists():
        try:
            with open(vh_path, "r", encoding="utf-8") as f:
                records = json.load(f)
            with get_cursor() as cur:
                for r in records:
                    cur.execute("""
                        INSERT OR IGNORE INTO validation_history
                        (id, timestamp, filename, status, action, confidence, message,
                         error_count, warning_count, row_count, user_id, session_id, run_id, details)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("id"), r.get("timestamp"), r.get("filename"),
                        r.get("status"), r.get("action"), r.get("confidence"),
                        r.get("message"), r.get("error_count"), r.get("warning_count"),
                        r.get("row_count"), r.get("user_id"), r.get("session_id"),
                        r.get("run_id"), json.dumps(r.get("details", {}), ensure_ascii=False),
                    ))
                stats["validation_history"] = len(records)
        except Exception as e:
            print(f"  validation_history migration error: {e}")

    # 2. cases/index.json + individual case files
    cases_dir = base_dir / "training_data" / "cases"
    if cases_dir.exists():
        try:
            for case_file in cases_dir.glob("*.json"):
                if case_file.name == "index.json":
                    continue
                with open(case_file, "r", encoding="utf-8") as f:
                    c = json.load(f)
                with get_cursor() as cur:
                    cur.execute("""
                        INSERT OR IGNORE INTO cases
                        (case_id, timestamp, confidence, was_auto_approved,
                         headers, normalized_headers, matches, human_corrections, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        c.get("case_id"), c.get("timestamp"), c.get("confidence"),
                        c.get("was_auto_approved", True),
                        json.dumps(c.get("headers", []), ensure_ascii=False),
                        json.dumps(c.get("normalized_headers", []), ensure_ascii=False),
                        json.dumps(c.get("matches", []), ensure_ascii=False),
                        json.dumps(c.get("human_corrections", {}), ensure_ascii=False),
                        json.dumps(c.get("metadata", {}), ensure_ascii=False),
                    ))
                    stats["cases"] += 1
        except Exception as e:
            print(f"  cases migration error: {e}")

    # 3. system_settings.json
    settings_path = base_dir / "config" / "system_settings.json"
    if settings_path.exists():
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
            with get_cursor() as cur:
                for key, value in settings.items():
                    cur.execute("""
                        INSERT OR REPLACE INTO system_settings (key, value, updated_at)
                        VALUES (?, ?, CURRENT_TIMESTAMP)
                    """, (key, json.dumps(value, ensure_ascii=False)))
                stats["settings"] = len(settings)
        except Exception as e:
            print(f"  settings migration error: {e}")

    # 4. error_rules.json
    rules_path = base_dir / "training_data" / "error_rules.json"
    if rules_path.exists():
        try:
            with open(rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            with get_cursor() as cur:
                for r in data.get("rules", []):
                    cur.execute("""
                        INSERT OR IGNORE INTO error_rules
                        (id, category, field, condition, severity, message, context_override, learned_at, source)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        r.get("id"), r.get("category"), r.get("field"),
                        r.get("condition"), r.get("severity"), r.get("message"),
                        json.dumps(r.get("context_override"), ensure_ascii=False) if r.get("context_override") else None,
                        r.get("learned_at"), r.get("source"),
                    ))
                    stats["error_rules"] += 1

                for p in data.get("learned_patterns", []):
                    cur.execute("""
                        INSERT INTO learned_patterns
                        (field, original_value, ai_said_error, correct_interpretation, context, learned_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        p.get("field"), p.get("original_value"),
                        p.get("ai_said_error", True),
                        p.get("correct_interpretation"),
                        json.dumps(p.get("context"), ensure_ascii=False) if p.get("context") else None,
                        p.get("learned_at"),
                    ))
        except Exception as e:
            print(f"  error_rules migration error: {e}")

    # 5. behavior_logs.json
    behavior_path = base_dir / "training_data" / "behavior_logs.json"
    if behavior_path.exists():
        try:
            with open(behavior_path, "r", encoding="utf-8") as f:
                logs = json.load(f)
            with get_cursor() as cur:
                for e in logs.get("events", []):
                    cur.execute("""
                        INSERT INTO behavior_events
                        (timestamp, action, context, session_id, analyzed)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        e.get("timestamp"), e.get("action"),
                        json.dumps(e.get("context", {}), ensure_ascii=False),
                        e.get("session_id"), e.get("analyzed", False),
                    ))
                    stats["behavior_events"] += 1
        except Exception as e:
            print(f"  behavior_logs migration error: {e}")

    print(f"  Migration complete: {stats}")
    return stats


def close_db() -> None:
    """DB 커넥션 종료."""
    global _connection
    if _connection:
        _connection.close()
        _connection = None
