from flask import Blueprint, request, jsonify, g
import psycopg2
import pandas as pd
import datetime
from .db import get_db, getArray

getter = Blueprint('getter', __name__)

@getter.record
def record_params(setup_state):
  app = setup_state.app
  getter.logger = app.logger

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

def createSelectReq(table_name, point_type, points_ids, period=None):
    suffix = ""
    if period:
        suffix = """ AND
            tbl.date_ >= '{:s}' AND
            tbl.date_ <= '{:s}'
        """.format(period['start'], period['end'])
    sql_params = {
        "point_type": point_type,
        "spd_table": "spd" if table_name == "train" else "spd_pred",
        "table_name": table_name,
        "bs_ids": ','.join(points_ids),
        "suffix": suffix
    }
    sql = """(
        SELECT 
            '{point_type}' as point_type, tbl.{spd_table}, 
            date_part('week', tbl.date_) as week, 
            date_part('year', tbl.date_) as year, tbl.id 
        FROM 
            {table_name} AS tbl 
        WHERE 
            tbl.id in ({bs_ids}){suffix})""".format(**sql_params)

    return sql

@getter.route('/bs/data', methods=['POST'])
def get_bs_data():
    params = request.get_json()
    if len(params['bs_ids']) == 0:
        return jsonify({}), 404
    selects = [createSelectReq("train", "train", params['bs_ids'])]
    selects += [createSelectReq("predict_" + model, model, params['bs_ids'], params['period']) for model in params['models']]
    sql_request = """
        SELECT point_type, AVG(spd), week, year, id 
        FROM ({:s}) AS OUT 
        GROUP BY point_type, week, year, id
        ORDER BY year ASC, week ASC;
    """.format(" UNION ".join(selects))
    
    points, columns = getArray(sql_request)

    getter.logger.info("Qty of points %d" % len(points))

    prev_models = [m for m in params['models']]
    prev_trains = [points[0], points[1]]
    prev_points = {m:None for m in params['models']}
    # we assume that points are sorted
    # we need to find previous point
    
    for pid, point in enumerate(points):
        if point[0] == 'train':
            prev_trains = [prev_trains[1], point]
        else:
            prev_models_tmp = []
            for model in prev_models:
                if point[0] == model:
                    if point[2] == prev_trains[-1][2] and point[3] == prev_trains[-1][3]:
                        prev_points[point[0]] = prev_trains[-1][:]
                    else:
                        prev_points[point[0]] = prev_trains[0][:]
                    #prev_points[point[0]] = prev_points[point[0]]
                else:
                    prev_models_tmp.append(model)
            prev_models = prev_models_tmp
    for model, point in prev_points.items():
        points.append((model,*point[1:]))

    points = sorted(points, key=lambda x: x[2] + x[3] * 100)
    
    return jsonify({"items": points, "col_names": columns}), 200