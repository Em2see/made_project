from flask import Blueprint, request, jsonify, make_response
import psycopg2
import pandas as pd
from datetime import datetime
from .db import get_db
from .models import get_models, models_info

runner = Blueprint('runner', __name__)

@runner.route('/model/<model_name>/status', methods=['GET'])
def model_status(model_name):
    cursor = get_db().cursor()
    sql_select_query = "SELECT * FROM train_runs WHERE name = '{:s}'".format(model_name)
    cursor.execute(sql_select_query)
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200

@runner.route('/model/<model_name>/info', methods=['GET'])
def model_info(model_name):
    if model_name not in models_info:
        return jsonify({}), 404
    return jsonify({"header": models_info[model_name][0], "info": models_info[model_name][1]}), 200

@runner.route('/model/<model_name>/train', methods=['GET'])
def model_train(model_name):
    models = get_models()
    # creating train_df
    train_df = getDF("train")
    setStartModel(model_name, "train")
    models[model_name].fit(train_df)
    setStopModel(model_name, "train")

@runner.route('/model/<model_name>/test', methods=['GET'])
def model_test(model_name):
    models = get_models()
    # creating train_df
    test_df = getDF("test")
    setStartModel(model_name, "test")
    result_df = models[model_name].predict(test_df)
    setStopModel(model_name, "test")

def getDF(tableName):
    if (tableName == 'test'):
        # here we need to join point table to test table
        sql_select_query = "SELECT * FROM test"
    else:
        sql_select_query = "SELECT * FROM train"
    cursor = get_db().cursor()
    cursor.execute(sql_select_query)
    records = cursor.fetchall()
    df = pd.DataFrame(records, columns = [val[0] for val in cursor.details])
    
    return df
    
def setStartModel(modelName, tableName="train"):
    cursor = get_db().cursor()
    sql_select_query = "INSERT INTO {:s}_runs (pid, model, start, stop) ".format(tableName, "0")
    dt_now = datetime.now().strftime("%d/%m/%y %hh:%mm")
    sql_select_query += " VALUES ({:d}, '{:s}', '{:s}', NULL)".format(0, modelName, dt_now)
    cursor.execute(sql_select_query)
    
def setStopModel(modelName, tableName="train"):
    cursor = get_db().cursor()
    sql_select_query = "UPDATE {:s}_runs SET stop = '{:s}' WHERE model = '{:s}'"
    dt_now = datetime.now().strftime("%d/%m/%y %hh:%mm")
    sql_select_query = sql_select_query.format(tableName, dt_now, modelName)
    cursor.execute(sql_select_query)

@runner.route('/model/run_all', methods=['GET'])
def model_train_all():
    models = get_models()
    # creating train_df
    train_df = getDF("train")

    #train all models
    for model_name, model in models.items():
        setStartModel(model_name, "train")
        model.fit(train_df)
        setStopModel(model_name, "train")

    return jsonify({}), 200
