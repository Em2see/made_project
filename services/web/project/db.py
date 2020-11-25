import psycopg2
from flask import g, current_app

def get_db():
    if 'conn' not in g:
        g.conn = psycopg2.connect(**current_app.config['DATABASE'])

    return g.conn


def close_db(e=None):
    conn = g.pop('conn', None)

    if conn is not None:
        conn.close()