from flask import g, current_app
from celery import Celery
import pandas as pd
from datetime import datetime
from time import sleep
import os
from .db import get_db, getArray, getDict, update, execMany
from .models import get_models, models_info, get_trained_model, set_trained_model
from . import app
from celery.app.control import Inspect
from datetime import datetime


def make_celery(app):
    icelery = Celery(app.import_name)
    icelery.config_from_object('project.celeryconfig')
    icelery.conf.update(app.config)

    TaskBase = icelery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    icelery.Task = ContextTask
    return icelery

celery = make_celery(app)

def get_tasks():
    inspect = Inspect(app=celery)
    return inspect

def getDF(tableName, period=None):
    if (tableName == 'test'):
        if period:
            #datetime.fromisoformat()
            sql_select_query = "SELECT * FROM test WHERE date_ >='{:s}' AND date_ <= '{:s}'".format(period['start'], period['end'])
        else:
            sql_select_query = "SELECT * FROM test"
    else:
        sql_select_query = "SELECT *  FROM train"
    
    records, cols = getArray(sql_select_query)
    df = pd.DataFrame(records, columns=cols)
    return df

def dropAllItems(tableName):
    update(f"DELETE FROM {tableName}")

def writeDF(tableName, result_df):
    columns = ['id', 'date_', 'x', 'y', 'tech', 'cap', 'height', 'azimuth', 'spd_pred']
    sql_query = "INSERT INTO {:s} ({:s}) VALUES %s;".format(tableName, ', '.join(columns))
    current_app.logger.info(result_df[columns].info())#.pipe(type_pipe)
    records = result_df[columns].to_records(index=False)
    execMany(sql_query, records)

def get_time_now():
    return datetime.now().strftime("%Y%m%d %H:%M:%S")

def setStartModel(modelName, tableName="train"):
    sql_select_query = "DELETE FROM run_{:s} WHERE model_name='{:s}'; ".format(tableName,modelName)
    sql_select_query += "INSERT INTO run_{:s} (pid, model_name, start, stop) ".format(tableName, "0")
    dt_now = get_time_now()
    sql_select_query += " VALUES ({:d}, '{:s}', '{:s}', NULL)".format(0, modelName, dt_now)
    update(sql_select_query)
    
def setStopModel(modelName, tableName="train"):
    sql_select_query = "UPDATE run_{:s} SET stop = '{:s}' WHERE model_name = '{:s}'"
    dt_now = get_time_now()
    sql_select_query = sql_select_query.format(tableName, dt_now, modelName)
    update(sql_select_query)

def getTaskState(task_id):
    state = celery.events.State()
    task = state.tasks.get(task_id)
    return task.name, task.uuid, task.info()

@celery.task()
def run_train(model_name):
    models = get_models()
    # creating train_df
    train_df = getDF("train")
    #train_df.to_csv(os.path.abspath('/models/exec.csv'))
    setStartModel(model_name, "train")
    models[model_name].train(train_df)
    set_trained_model(model_name, models[model_name])
    setStopModel(model_name, "train")
    return "done"

@celery.task()
def run_predict(model_name, period):
    # creating train_df
    test_df = getDF("test", period)
    setStartModel(model_name, "test")
    model = get_trained_model(model_name)
    result_df = model.predict(test_df)
    dropAllItems(f"predict_{model_name}")
    writeDF(f"predict_{model_name}", result_df)
    setStopModel(model_name, "test")
    return "done"

@celery.task()
def predict_all():
    models = get_models()
    # creating test_df
    test_df = getDF("test")

    #train all models
    for model_name, model in models.items():
        setStartModel(model_name, "test")
        result_df = model.predict(test_df)
        writeDF(f"predict_{model_name}", result_df)
        setStopModel(model_name, "test")
    return "done"

@celery.task()
def train_all():
    models = get_models()
    # creating train_df
    train_df = getDF("train")

    #train all models
    for model_name, model in models.items():
        setStartModel(model_name, "train")
        model.train(train_df)
        setStopModel(model_name, "train")
    return "done"
