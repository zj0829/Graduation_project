import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta

BJ_TZ = timezone(timedelta(hours=8))

def bj_now():
    return datetime.now(BJ_TZ).strftime("%Y-%m-%d %H:%M:%S")

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "pentest.db")


def _get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS test_reports (
            test_id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            requirements TEXT,
            tools TEXT,
            tool_strategy TEXT DEFAULT 'auto',
            report_format TEXT DEFAULT 'markdown',
            mcp_results TEXT,
            analysis TEXT,
            report TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            model TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            msg_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            tools_info TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)
        )
    """)
    conn.commit()
    conn.close()


def save_report(test_id, target, requirements, tools, tool_strategy, report_format, mcp_results, analysis, report):
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO test_reports (test_id, target, requirements, tools, tool_strategy, report_format, mcp_results, analysis, report, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            test_id,
            target,
            requirements,
            json.dumps(tools, ensure_ascii=False),
            tool_strategy,
            report_format,
            json.dumps(mcp_results, ensure_ascii=False) if isinstance(mcp_results, dict) else str(mcp_results),
            analysis or "",
            report or "",
            bj_now(),
        ),
    )
    conn.commit()
    conn.close()


def get_report(test_id):
    conn = _get_conn()
    row = conn.execute("SELECT * FROM test_reports WHERE test_id = ?", (test_id,)).fetchone()
    conn.close()
    if not row:
        return None
    return _row_to_dict(row)


def list_reports(limit=50, offset=0):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT test_id, target, requirements, tools, tool_strategy, created_at FROM test_reports ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM test_reports").fetchone()[0]
    conn.close()
    return {"total": total, "reports": [_row_to_dict(r) for r in rows]}


def delete_report(test_id):
    conn = _get_conn()
    conn.execute("DELETE FROM test_reports WHERE test_id = ?", (test_id,))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0


def _row_to_dict(row):
    d = dict(row)
    if "tools" in d and d["tools"]:
        try:
            d["tools"] = json.loads(d["tools"])
        except (json.JSONDecodeError, TypeError):
            pass
    if "mcp_results" in d and d["mcp_results"]:
        try:
            d["mcp_results"] = json.loads(d["mcp_results"])
        except (json.JSONDecodeError, TypeError):
            pass
    return d


def create_chat_session(session_id, title, model):
    conn = _get_conn()
    now = bj_now()
    conn.execute(
        "INSERT INTO chat_sessions (session_id, title, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, title, model, now, now),
    )
    conn.commit()
    conn.close()


def save_chat_message(session_id, role, content, tools_info=None):
    conn = _get_conn()
    now = bj_now()
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, content, tools_info, created_at) VALUES (?, ?, ?, ?, ?)",
        (session_id, role, content, json.dumps(tools_info, ensure_ascii=False) if tools_info else None, now),
    )
    conn.execute(
        "UPDATE chat_sessions SET updated_at = ? WHERE session_id = ?",
        (now, session_id),
    )
    conn.commit()
    conn.close()


def list_chat_sessions(limit=50):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT session_id, title, model, created_at, updated_at FROM chat_sessions ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chat_messages(session_id):
    conn = _get_conn()
    rows = conn.execute(
        "SELECT msg_id, role, content, tools_info, created_at FROM chat_messages WHERE session_id = ? ORDER BY msg_id ASC",
        (session_id,),
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        if d.get("tools_info"):
            try:
                d["tools_info"] = json.loads(d["tools_info"])
            except (json.JSONDecodeError, TypeError):
                pass
        result.append(d)
    return result


def delete_chat_session(session_id):
    conn = _get_conn()
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM chat_sessions WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()
    return True


init_db()
