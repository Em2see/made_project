from flask import Blueprint, request, jsonify, make_response
import psycopg2
import pandas as pd
import datetime
from .db import get_db
import sys
import os

runner = Blueprint('runner', __name__)

models_path = os.path.abspath("/")
if models_path not in sys.path:
    sys.path.append(models_path)
    from models import ARMA_model, Boosting_model, Linear_model
    from models import models_info

@runner.route('/model/<model_id>/status', methods=['GET'])
def model_status(model_id):
    cursor = get_db().cursor()
    sql_select_query = """select * from models_run where id = %s"""
    cursor.execute(sql_select_query, (model_id, ))
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200

@runner.route('/model/<model_name>/info', methods=['GET'])
def model_info(model_name):
    if model_name not in models_info:
        return jsonify({}), 404
    return jsonify({"header": models_info[model_name][0], "info": models_info[model_name][1]}), 200

def get_train_df():
    cursor = get_db().cursor()
    sql_select_query = """select * from train"""
    cursor.execute(sql_select_query)
    records = cursor.fetchall()
    if len(records) == 0:
        pass
    df = pd.DataFrame(records)
    return df


@runner.route('/model/<model_name>/run', methods=['GET'])
def model_run(model_name):
    models = {
        "arma": ARMA_model,
        "boosting": Boosting_model,
        "linear": Linear_model
    }
    Model = models[model_name]
    train_df = get_train_df()
    model = Model()
    model.train(train_df)

@runner.route('/model/run_all', methods=['GET'])
def model_run_all():
    return jsonify({}), 200
