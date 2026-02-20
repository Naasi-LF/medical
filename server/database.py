"""MongoDB connection and collection helpers."""

from __future__ import annotations

import logging

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import ConnectionFailure

from gastric_agent.config import get_config

logger = logging.getLogger(__name__)

_client: MongoClient | None = None
_db: Database | None = None


def _get_db() -> Database:
    global _client, _db
    if _db is not None:
        return _db
    cfg = get_config()
    try:
        _client = MongoClient(cfg.mongo_uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    except ConnectionFailure:
        logger.error("Failed to connect to MongoDB at %s", cfg.mongo_uri)
        raise
    _db = _client[cfg.mongo_db_name]

    _db["users"].create_index("username", unique=True)
    _db["conversations"].create_index("user_id")
    _db["conversations"].create_index("updated_at")
    _db["messages"].create_index("conversation_id")
    _db["messages"].create_index("created_at")

    return _db


def users_col() -> Collection:
    return _get_db()["users"]


def conversations_col() -> Collection:
    return _get_db()["conversations"]


def messages_col() -> Collection:
    return _get_db()["messages"]
