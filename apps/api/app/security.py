import hashlib
import hmac
import secrets
import threading
import time
from datetime import timedelta
from fastapi import Depends, HTTPException, Request
from .config import settings
from .db import Member, Session, SessionLocal, User, now

def password_hash(password):
    salt = secrets.token_hex(16)
    value = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()
    return "$".join(["pbkdf2_sha256", "600000", salt, value])

def verify_password(password, encoded):
    _, rounds, salt, digest = encoded.split("$")
    computed = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
    return hmac.compare_digest(digest, computed)

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def get_db():
    with SessionLocal() as db:
        yield db

def current_user(request: Request, db=Depends(get_db)):
    token = request.cookies.get("insyvera_session", "")
    session = db.get(Session, token_hash(token))
    if not session or session.expires_at.replace(tzinfo=now().tzinfo) <= now():
        raise HTTPException(401, "Sign in to continue.")
    user = db.get(User, session.user_id)
    if not user:
        raise HTTPException(401, "Session expired.")
    return user

def authorize(db, workspace, user):
    if not db.get(Member, (workspace, user.id)):
        raise HTTPException(404, "Workspace not found.")

def create_session(db, user, response):
    token = secrets.token_urlsafe(40)
    db.add(Session(token=token_hash(token), user_id=user.id,
        expires_at=now() + timedelta(hours=settings.session_hours)))
    response.set_cookie("insyvera_session", token, httponly=True, samesite="strict",
        secure=settings.secure_cookie, max_age=settings.session_hours * 3600, path="/")

class RateLimit:
    def __init__(self):
        self.entries = {}
        self.lock = threading.Lock()
    def check(self, key, maximum=15, seconds=60):
        if settings.redis_url:
            import redis
            client = redis.Redis.from_url(settings.redis_url)
            bucket = f"ratelimit:{key}:{int(time.time()) // seconds}"
            count = client.incr(bucket)
            if count == 1:
                client.expire(bucket, seconds + 1)
            if count > maximum:
                raise HTTPException(429, "Too many requests. Try again shortly.")
            return
        with self.lock:
            current = time.monotonic()
            if len(self.entries) > 10000:
                self.entries = {k: v for k, v in self.entries.items() if v[-1] > current - seconds}
            values = [v for v in self.entries.get(key, []) if v > current - seconds]
            if len(values) >= maximum:
                raise HTTPException(429, "Too many requests. Try again shortly.")
            self.entries[key] = values + [current]

limiter = RateLimit()
