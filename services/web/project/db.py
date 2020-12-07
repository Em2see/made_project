from psycopg2 import connect
from psycopg2.extras import execute_values
from psycopg2.extensions import register_adapter, AsIs, DateFromPy
import numpy as np
from flask import g, current_app
from sqlalchemy import create_engine
import redis


def addapt_numpy_float64(numpy_float64):
    return AsIs(numpy_float64)
def addapt_numpy_int64(numpy_int64):
    return AsIs(numpy_int64)
def addapt_numpy_datetime(numpy_datetime):
    return DateFromPy(numpy_datetime)


register_adapter(np.float64, addapt_numpy_float64)
register_adapter(np.int64, addapt_numpy_int64)
register_adapter(np.datetime64, addapt_numpy_datetime)

def get_db():
    if 'conn' not in g:
        g.conn = connect(**current_app.config['DATABASE'])
    return g.conn
    
def get_engine():
    if 'engine' not in g:
        g.engine = create_engine(current_app.config['ENGINE'])
    return g.engine

def get_models_storage():
    if 'models_storage' not in g:
        g.models_storage = redis.Redis(**current_app.config['REDIS_MODELS'])
    return g.models_storage

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
    
def execMany(query, values):
    conn = get_db()
    cursor = conn.cursor()
    current_app.logger.info(query)
    execute_values(cursor, query, values)
    conn.commit()

def close_db(e=None):
    conn = g.pop('conn', None)
    if conn is not None:
        conn.close()