from flask import Blueprint, request, jsonify, make_response
import psycopg2
import pandas as pd
from datetime import datetime
from time import sleep
from .db import get_db, getArray, getDict, update
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
    #models[model_name].fit(train_df)
    setStopModel(model_name, "train")
    return jsonify({"shape": train_df.shape}), 200

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
    records, cols = getArray(sql_select_query)
    df = pd.DataFrame(records, columns=cols)
    
    return df

def get_time_now():
    return datetime.now().strftime("%Y%m%d %H:%M:%S")

def setStartModel(modelName, tableName="train"):
    sql_select_query = "DELETE FROM {:s}_run WHERE model_name='{:s}'; ".format(tableName,modelName)
    sql_select_query += "INSERT INTO {:s}_run (pid, model_name, start, stop) ".format(tableName, "0")
    dt_now = get_time_now()
    sql_select_query += " VALUES ({:d}, '{:s}', '{:s}', NULL)".format(0, modelName, dt_now)
    update(sql_select_query)
    
def setStopModel(modelName, tableName="train"):
    sql_select_query = "UPDATE {:s}_run SET stop = '{:s}' WHERE model_name = '{:s}'"
    dt_now = get_time_now()
    sql_select_query = sql_select_query.format(tableName, dt_now, modelName)
    update(sql_select_query)

@runner.route('/model/predict_all', methods=['GET'])
def model_predict_all():
    models = get_models()
    # creating test_df
    test_df = getDF("test")

    #train all models
    for model_name, model in models.items():
        setStartModel(model_name, "test")
        model.predict(test_df)
        setStopModel(model_name, "test")

    return jsonify({}), 200

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
