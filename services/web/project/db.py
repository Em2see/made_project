import psycopg2
from flask import g, current_app

def get_db():
    if 'conn' not in g:
        g.conn = psycopg2.connect(**current_app.config['DATABASE'])

    return g.conn

def getDict(sql_select_query):
    cursor = get_db().cursor()
    cursor.execute(sql_select_query)
    results = cursor.fetchall()
    col_names = [val[0] for val in cursor.description]
    out = []
    for res in results:
        out.append({k:v for k,v in zip(col_names, res)})
    return out

def getArray(sql_select_query):
    cursor = get_db().cursor()
    cursor.execute(sql_select_query)
    col_names = [val[0] for val in cursor.description]
    results = cursor.fetchall()
    current_app.logger.info(sql_select_query)
    current_app.logger.info(len(results))
    return results, col_names

def update(sql_select_query):
    conn = get_db()
    cursor = conn.cursor()
    current_app.logger.info(sql_select_query)
    cursor.execute(sql_select_query)
    conn.commit()

def close_db(e=None):
    conn = g.pop('conn', None)

    if conn is not None:
        conn.close()