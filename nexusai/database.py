"""
database.py — NexusAI SQLite layer
Tables: users, sessions, conversations, messages, daily_usage
"""
import os, sqlite3, hashlib, secrets
from datetime import datetime, date, timedelta

DB = "/tmp/nexus.db" if os.getenv("VERCEL") else "nexus.db"
PLAN_LIMITS = {"free": 50, "pro": 500, "enterprise": 999999}


def _conn():
    return sqlite3.connect(DB, timeout=30.0)


def init_db():
    c = _conn()
    try:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    NOT NULL UNIQUE,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            salt          TEXT    NOT NULL,
            plan          TEXT    NOT NULL DEFAULT 'free',
            created_at    TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            user_id    INTEGER NOT NULL,
            expires_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS conversations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sid        TEXT    NOT NULL UNIQUE,
            user_id    INTEGER NOT NULL,
            title      TEXT    DEFAULT 'New Chat',
            created_at TEXT    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sid       TEXT NOT NULL,
            role      TEXT NOT NULL,
            content   TEXT NOT NULL,
            file_name TEXT,
            file_type TEXT,
            ts        TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS daily_usage (
            user_id    INTEGER NOT NULL,
            day        TEXT    NOT NULL,
            count      INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(user_id, day)
        );
        """)
        c.commit()
    finally:
        c.close()


# ── Password ─────────────────────────────────────────────────────────────────
def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt.encode(), 200000).hex()

def hash_pw(pw):
    s = secrets.token_hex(32)
    return _hash(pw, s), s

def verify_pw(pw, h, s):
    return secrets.compare_digest(_hash(pw, s), h)


# ── Users ─────────────────────────────────────────────────────────────────────
def create_user(username, email, password):
    h, s = hash_pw(password)
    c = _conn()
    try:
        cursor = c.execute("INSERT INTO users(username,email,password_hash,salt,plan,created_at) VALUES(?,?,?,?,?,?)",
                           (username, email, h, s, "free", datetime.now().isoformat()))
        uid = cursor.lastrowid
        c.commit()
        return {"id": uid, "username": username, "email": email, "plan": "free"}
    except sqlite3.IntegrityError:
        return None
    finally:
        c.close()

def get_user_by_email(email):
    c = _conn()
    try:
        r = c.execute("SELECT id,username,email,password_hash,salt,plan FROM users WHERE email=?", (email,)).fetchone()
        return {"id":r[0],"username":r[1],"email":r[2],"password_hash":r[3],"salt":r[4],"plan":r[5]} if r else None
    finally:
        c.close()

def get_user_by_id(uid):
    c = _conn()
    try:
        r = c.execute("SELECT id,username,email,plan FROM users WHERE id=?", (uid,)).fetchone()
        return {"id":r[0],"username":r[1],"email":r[2],"plan":r[3]} if r else None
    finally:
        c.close()

def upgrade_plan(uid, plan):
    c = _conn()
    try:
        c.execute("UPDATE users SET plan=? WHERE id=?", (plan, uid))
        c.commit()
    finally:
        c.close()


# ── Sessions ──────────────────────────────────────────────────────────────────
def create_session(uid):
    token = secrets.token_urlsafe(48)
    exp   = (datetime.now() + timedelta(days=7)).isoformat()
    c = _conn()
    try:
        c.execute("INSERT INTO sessions(token,user_id,expires_at) VALUES(?,?,?)", (token, uid, exp))
        c.commit()
        return token
    finally:
        c.close()

def get_session_user(token):
    c = _conn()
    uid = None
    try:
        r = c.execute("SELECT user_id,expires_at FROM sessions WHERE token=?", (token,)).fetchone()
        if not r:
            return None
        if datetime.now().isoformat() > r[1]:
            c.close()
            delete_session(token)
            return None
        uid = r[0]
    finally:
        try:
            c.close()
        except sqlite3.ProgrammingError:
            pass # already closed
            
    if uid is not None:
        return get_user_by_id(uid)
    return None

def delete_session(token):
    c = _conn()
    try:
        c.execute("DELETE FROM sessions WHERE token=?", (token,))
        c.commit()
    finally:
        c.close()


# ── Rate limit ────────────────────────────────────────────────────────────────
def get_usage(uid):
    u = get_user_by_id(uid)
    plan  = u["plan"] if u else "free"
    limit = PLAN_LIMITS.get(plan, 50)
    today = date.today().isoformat()
    c = _conn()
    try:
        r = c.execute("SELECT count FROM daily_usage WHERE user_id=? AND day=?", (uid, today)).fetchone()
        used = r[0] if r else 0
        return {"used": used, "limit": limit, "remaining": max(0, limit - used), "plan": plan}
    finally:
        c.close()

def bump_usage(uid):
    today = date.today().isoformat()
    c = _conn()
    try:
        c.execute("INSERT INTO daily_usage(user_id,day,count) VALUES(?,?,1) "
                  "ON CONFLICT(user_id,day) DO UPDATE SET count=count+1", (uid, today))
        c.commit()
    finally:
        c.close()

def is_limited(uid):
    u = get_usage(uid); return u["used"] >= u["limit"]


# ── Chats ─────────────────────────────────────────────────────────────────────
def save_msg(sid, uid, role, content, file_name=None, file_type=None):
    c = _conn()
    try:
        c.execute("INSERT INTO messages(sid,role,content,file_name,file_type,ts) VALUES(?,?,?,?,?,?)",
                  (sid, role, content, file_name, file_type, datetime.now().isoformat()))
        c.execute("INSERT OR IGNORE INTO conversations(sid,user_id,title,created_at) VALUES(?,?,?,?)",
                  (sid, uid, "New Chat", datetime.now().isoformat()))
        if role == "user":
            t = (content[:42]+"...") if len(content)>42 else content
            c.execute("UPDATE conversations SET title=? WHERE sid=? AND title='New Chat'", (t, sid))
        c.commit()
    finally:
        c.close()

def get_msgs(sid):
    c = _conn()
    try:
        rows = c.execute("SELECT role,content,file_name,file_type,ts FROM messages WHERE sid=? ORDER BY id", (sid,)).fetchall()
        return [{"role":r[0],"content":r[1],"file_name":r[2],"file_type":r[3],"ts":r[4]} for r in rows]
    finally:
        c.close()

def get_convs(uid, search=""):
    c = _conn()
    try:
        if search:
            rows = c.execute("SELECT sid,title,created_at FROM conversations WHERE user_id=? AND title LIKE ? ORDER BY id DESC LIMIT 60",
                             (uid, f"%{search}%")).fetchall()
        else:
            rows = c.execute("SELECT sid,title,created_at FROM conversations WHERE user_id=? ORDER BY id DESC LIMIT 60", (uid,)).fetchall()
        return [{"sid":r[0],"title":r[1],"created_at":r[2]} for r in rows]
    finally:
        c.close()

def del_conv(sid, uid):
    c = _conn()
    try:
        c.execute("DELETE FROM messages WHERE sid=?", (sid,))
        c.execute("DELETE FROM conversations WHERE sid=? AND user_id=?", (sid, uid))
        c.commit()
    finally:
        c.close()
