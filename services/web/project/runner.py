from flask import Blueprint, request, jsonify, make_response, current_app, url_for
import pandas as pd
from datetime import datetime
from time import sleep
import os
from celery.result import AsyncResult
from .db import get_db, getArray, getDict, update, execMany
from .models import get_models, models_info, get_trained_model, set_trained_model, is_model_trained
from datetime import datetime
import json

runner = Blueprint('runner', __name__)

@runner.record
def record_params(setup_state):
  app = setup_state.app
  runner.logger = app.logger

@runner.route('/model/<model_name>/status', methods=['GET'])
def model_status(model_name):
    res = getDict("SELECT * FROM run_train WHERE model_name='{:s}'".format(model_name))
    if len(res) == 0:
        return jsonify({}), 404
    return jsonify(res), 200

def parse_tasks(input_dict, status):
    out = []
    for runner_name, task_list in input_dict.items():
        for task in task_list:
            task = [
                task['name'].split('.')[-1],
                json.dumps(task['args']),
                datetime.fromtimestamp(task['time_start']),
                task['hostname'],
                task['worker_pid'],
                status
            ]
            out.append(task)
    return out

@runner.route('/model/get_tasks')
def get_tasks_info():
    from .tasks import get_tasks
    i = get_tasks()

    out = []
    out += parse_tasks(i.active(), "active")
    out += parse_tasks(i.scheduled(), "scheduled")
    out += parse_tasks(i.reserved(), "reserved")
    return jsonify(out), 200
    
@runner.route('/model/get_tasks_raw')
def get_tasks_info_raw():
    from .tasks import get_tasks
    i = get_tasks()
    return jsonify({"scheduled": i.scheduled(), 
                    "active": i.active(), 
                    "reserved": i.reserved(), 
                    "destination": i.destination, 
                    "connection": i.connection
                    }), 200

@runner.route('/model/<model_name>/info', methods=['GET'])
def model_info(model_name):
    if model_name not in models_info:
        return jsonify({}), 404
    return jsonify({"header": models_info[model_name][0], "info": models_info[model_name][1]}), 200

@runner.route('/model/<model_name>/train', methods=['GET'])
def model_train(model_name):
    from .tasks import run_train
    task = run_train.delay(model_name)
    return jsonify({}), 202, {'Location': url_for('runner.taskstatus',
                                                  task_id=task.id, task_type='run_train')}
                                                
@runner.route('/model/<task_id>/<task_type>/task_status')
def taskstatus(task_id, task_type):
    from .tasks import run_train, run_predict, predict_all, train_all
    func = eval(task_type)
    task = func.AsyncResult(task_id)
    return jsonify({"result": task.result, "ready": task.ready(), "state": task.state, "status": task.status}), 200

@runner.route('/model/<model_name>/predict', methods=['POST'])
def model_predict(model_name):
    params = request.get_json()
    runner.logger.info(params)
    from .tasks import run_predict
    if not is_model_trained(model_name):
        return jsonify({"response": "model hasn't been trained"}), 404
    task = run_predict.delay(model_name, params)
    runner.logger.info(task)
    return jsonify({}), 202, {'Location': url_for('runner.taskstatus',
                                                  task_id=task.id, task_type='run_predict')}

@runner.route('/model/predict_all', methods=['GET'])
def model_predict_all():
    from .tasks import predict_all
    task = predict_all.delay()

    return jsonify({}), 202, {'Location': url_for('runner.taskstatus',
                                                  task_id=task.id, task_type='predict_all')}

@runner.route('/model/run_all', methods=['GET'])
def model_train_all():
    from .tasks import train_all
    task = train_all.delay()

    return jsonify({}), 202, {'Location': url_for('runner.taskstatus',
                                                  task_id=task.id, task_type='train_all')}
