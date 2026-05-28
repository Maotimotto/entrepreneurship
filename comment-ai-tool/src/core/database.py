"""数据库模块 — SQLite 持久化"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Optional
from src.models.comment import Lead, LeadScore, Platform
from src.core.logger import logging

logger = logging.getLogger(__name__)

DB_PATH = os.environ.get("COMMENT_AI_DB", "comment_ai.db")


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """初始化数据库表"""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS leads (
            id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            author_id TEXT NOT NULL,
            author_name TEXT NOT NULL,
            first_comment_id TEXT NOT NULL,
            lead_score REAL NOT NULL,
            status TEXT DEFAULT 'new',
            tags TEXT DEFAULT '[]',
            notes TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS scores (
            comment_id TEXT PRIMARY KEY,
            score REAL NOT NULL,
            intent TEXT NOT NULL,
            urgency TEXT NOT NULL,
            keywords TEXT DEFAULT '[]',
            reasoning TEXT DEFAULT '',
            analyzed_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analysis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comment_content TEXT NOT NULL,
            author_name TEXT NOT NULL,
            platform TEXT NOT NULL,
            score REAL,
            intent TEXT,
            reply TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
        CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score DESC);
        CREATE INDEX IF NOT EXISTS idx_scores_intent ON scores(intent);
    """)
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {DB_PATH}")


class LeadStore:
    """潜客存储"""

    @staticmethod
    def save(lead: Lead):
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO leads (id, platform, author_id, author_name, first_comment_id, lead_score, status, tags, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.id, lead.platform.value, lead.author_id, lead.author_name,
            lead.first_comment_id, lead.lead_score, lead.status,
            json.dumps(lead.tags), lead.notes,
            lead.created_at.isoformat() if lead.created_at else datetime.now().isoformat(),
            lead.updated_at.isoformat() if lead.updated_at else None,
        ))
        conn.commit()
        conn.close()

    @staticmethod
    def get(lead_id: str) -> Optional[Lead]:
        conn = get_db()
        row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
        conn.close()
        if not row:
            return None
        return Lead(
            id=row["id"], platform=Platform(row["platform"]),
            author_id=row["author_id"], author_name=row["author_name"],
            first_comment_id=row["first_comment_id"], lead_score=row["lead_score"],
            status=row["status"], tags=json.loads(row["tags"]),
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
        )

    @staticmethod
    def list_all(status: Optional[str] = None, min_score: float = 0.0) -> list[Lead]:
        conn = get_db()
        query = "SELECT * FROM leads WHERE lead_score >= ?"
        params = [min_score]
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY lead_score DESC"
        rows = conn.execute(query, params).fetchall()
        conn.close()
        return [Lead(
            id=r["id"], platform=Platform(r["platform"]),
            author_id=r["author_id"], author_name=r["author_name"],
            first_comment_id=r["first_comment_id"], lead_score=r["lead_score"],
            status=r["status"], tags=json.loads(r["tags"]),
            notes=r["notes"],
            created_at=datetime.fromisoformat(r["created_at"]) if r["created_at"] else None,
            updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else None,
        ) for r in rows]

    @staticmethod
    def update_status(lead_id: str, status: str) -> bool:
        conn = get_db()
        cur = conn.execute("UPDATE leads SET status = ?, updated_at = ? WHERE id = ?",
                           (status, datetime.now().isoformat(), lead_id))
        conn.commit()
        conn.close()
        return cur.rowcount > 0

    @staticmethod
    def count() -> int:
        conn = get_db()
        n = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        conn.close()
        return n

    @staticmethod
    def stats() -> dict:
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        by_status = {}
        for row in conn.execute("SELECT status, COUNT(*) as cnt FROM leads GROUP BY status"):
            by_status[row["status"]] = row["cnt"]
        by_score = {"high": 0, "medium": 0, "low": 0}
        for row in conn.execute("""
            SELECT
                SUM(CASE WHEN lead_score >= 0.7 THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN lead_score >= 0.4 AND lead_score < 0.7 THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN lead_score < 0.4 THEN 1 ELSE 0 END) as low
            FROM leads
        """):
            by_score = {"high": row["high"] or 0, "medium": row["medium"] or 0, "low": row["low"] or 0}
        conn.close()
        return {"total": total, "by_status": by_status, "by_score_level": by_score}


class ScoreStore:
    """评分存储"""

    @staticmethod
    def save(score: LeadScore):
        conn = get_db()
        conn.execute("""
            INSERT OR REPLACE INTO scores (comment_id, score, intent, urgency, keywords, reasoning, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (score.comment_id, score.score, score.intent, score.urgency,
              json.dumps(score.keywords), score.reasoning, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def count() -> int:
        conn = get_db()
        n = conn.execute("SELECT COUNT(*) FROM scores").fetchone()[0]
        conn.close()
        return n


class AnalysisLogStore:
    """分析日志"""

    @staticmethod
    def log(comment: str, author: str, platform: str, score: float, intent: str, reply: str):
        conn = get_db()
        conn.execute("""
            INSERT INTO analysis_log (comment_content, author_name, platform, score, intent, reply, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (comment, author, platform, score, intent, reply, datetime.now().isoformat()))
        conn.commit()
        conn.close()
