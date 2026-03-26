"""Progress tracking — SQLite backed topic mastery"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path("data/db/progress.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _get_conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS topic_scores (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject     TEXT NOT NULL,
            topic       TEXT NOT NULL,
            score       REAL DEFAULT 0,
            interactions INTEGER DEFAULT 0,
            last_seen   TEXT,
            UNIQUE(subject, topic)
        );

        CREATE TABLE IF NOT EXISTS interactions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            subject   TEXT,
            query     TEXT,
            intent    TEXT,
            timestamp TEXT
        );

        CREATE TABLE IF NOT EXISTS quiz_results (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            subject   TEXT,
            topic     TEXT,
            correct   INTEGER,
            total     INTEGER,
            timestamp TEXT
        );
        """)


init_db()

# Intent → score delta (positive = topic is getting stronger)
INTENT_SCORE = {
    "topic_explain":  5,
    "question_solve": 8,
    "quiz":           10,
    "study_plan":     2,
    "weak_area":      3,
    "general":        2,
}


def update_topic_score(subject: str, topic: str, intent: str):
    delta = INTENT_SCORE.get(intent, 2)
    now   = datetime.now().isoformat()
    with _get_conn() as conn:
        conn.execute("""
            INSERT INTO topic_scores (subject, topic, score, interactions, last_seen)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(subject, topic) DO UPDATE SET
                score        = MIN(score + ?, 100),
                interactions = interactions + 1,
                last_seen    = ?
        """, (subject, topic, delta, now, delta, now))


def log_interaction(subject: str, query: str, intent: str):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO interactions (subject, query, intent, timestamp) VALUES (?,?,?,?)",
            (subject, query[:300], intent, datetime.now().isoformat()),
        )


def log_quiz_result(subject: str, topic: str, correct: int, total: int):
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO quiz_results (subject, topic, correct, total, timestamp) VALUES (?,?,?,?,?)",
            (subject, topic, correct, total, datetime.now().isoformat()),
        )
        # Boost score based on performance
        pct   = correct / max(total, 1) * 100
        bonus = int(pct / 10)
        conn.execute("""
            INSERT INTO topic_scores (subject, topic, score, interactions, last_seen)
            VALUES (?, ?, ?, 1, ?)
            ON CONFLICT(subject, topic) DO UPDATE SET
                score        = MIN(score + ?, 100),
                interactions = interactions + 1,
                last_seen    = ?
        """, (subject, topic, bonus, datetime.now().isoformat(),
               bonus, datetime.now().isoformat()))


def get_topic_scores(subject: str) -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT topic, score, interactions, last_seen FROM topic_scores "
            "WHERE subject=? ORDER BY score DESC",
            (subject,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_weak_topics(subject: str, threshold: float = 40.0) -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT topic, score FROM topic_scores "
            "WHERE subject=? AND score < ? ORDER BY score ASC LIMIT 5",
            (subject, threshold)
        ).fetchall()
    return [dict(r) for r in rows]


def get_interaction_counts(subject: str) -> dict:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT intent, COUNT(*) as cnt FROM interactions "
            "WHERE subject=? GROUP BY intent",
            (subject,)
        ).fetchall()
    return {r["intent"]: r["cnt"] for r in rows}


def get_recent_interactions(subject: str, limit: int = 10) -> list:
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT query, intent, timestamp FROM interactions "
            "WHERE subject=? ORDER BY timestamp DESC LIMIT ?",
            (subject, limit)
        ).fetchall()
    return [dict(r) for r in rows]


def get_quiz_stats(subject: str) -> dict:
    with _get_conn() as conn:
        row = conn.execute(
            "SELECT SUM(correct) as total_correct, SUM(total) as total_attempted "
            "FROM quiz_results WHERE subject=?",
            (subject,)
        ).fetchone()
    if row and row["total_attempted"]:
        return {
            "correct":   row["total_correct"] or 0,
            "attempted": row["total_attempted"] or 0,
            "pct":       round((row["total_correct"] or 0) / row["total_attempted"] * 100, 1),
        }
    return {"correct": 0, "attempted": 0, "pct": 0}
