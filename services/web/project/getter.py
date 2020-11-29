from flask import Blueprint, request, jsonify, g
import psycopg2
import pandas as pd
import datetime
from .db import get_db, getArray

getter = Blueprint('getter', __name__)

@getter.route('/get_id/simple/<id>', methods=['GET','POST'])
def simple_id(id):
    cursor = get_db().cursor()
    sql_select_query = """select * from test_pred_simple where id = %s"""
    cursor.execute(sql_select_query, (id, ))
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200

@getter.route('/get_date/simple/<date>', methods=['GET','POST'])
def simple_date(date):
    cursor = get_db().cursor()
    sql_select_query = """select * from test_pred_simple where date_ = %s"""
    cursor.execute(sql_select_query, (id, ))
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200
    
@getter.route('/bs/data', methods=['POST'])
def get_bs_data():
    params = request.get_json()
    if len(params['bs_ids']) == 0:
        return jsonify({}), 404
    bs_ids = ','.join(params['bs_ids'])
    sql_request = """
        SELECT point_type, AVG(spd), week, year, id FROM
        ((SELECT 'pred' as point_type, pred.spd, date_part('week', pred.date_) as week, date_part('year', pred.date_) as year, pred.id FROM test_pred_simple AS pred WHERE pred.id in ({:s})) 
        UNION
        (SELECT 'train' as point_type, train.spd, date_part('week', train.date_) as week, date_part('year', train.date_) as year, train.id FROM train WHERE train.id in ({:s})))
        AS OUT GROUP BY point_type, week, year, id;
    """
    sql_request = sql_request.format(bs_ids, bs_ids)
    points, columns = getArray(sql_request)
    points = sorted(points, key=lambda x: x[2] + x[3] * 100)
    npoints = points[:-10] + [["pred"] + list(p[1:]) for p in points[-10:]]
    return jsonify({"items": npoints, "col_names": columns}), 200