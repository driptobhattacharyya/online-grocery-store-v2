import os
import sqlite3

from flask import current_app, g


def database_path():
    env_path = os.environ.get("DATABASE_PATH")
    if env_path:
        return env_path
    return current_app.config["DATABASE_PATH"]


def get_db():
    if "db" not in g:
        path = database_path()
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        g.db = connection
    return g.db


def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
