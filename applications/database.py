import sqlite3
from flask import g
from flask import current_app as app


DATABASE = 'grocery_take1.db'

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
    return g.db


def close_db(exception=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
