from flask import Blueprint, request, jsonify, g
import psycopg2
import pandas as pd
import datetime
from .db import get_db

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
    
@getter.route('/recalc', methods=['GET'])
def run_calcs():
    pass
    return make_response(jsonify({}), 200)