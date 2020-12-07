import sys
import os
from flask import g, current_app
from models import models_info, models_class
from .db import get_models_storage
import pickle

def get_models_info():
    if 'model_info' not in g:
        g.models_info = models_info
    return g.models_info

def get_models():
    storage = get_models_storage()
    if 'models' not in g:
        g.models = {k:m() for k,m in models_class.items()}
    return g.models

def get_trained_model(model_name):
    storage = get_models_storage()
    if storage.exists(model_name):
        # we understand it's a dangerous approach
        # however we don't have enought time to save it to json
        return pickle.loads(storage.get(model_name))
    return None

def set_trained_model(model_name, model):
    storage = get_models_storage()
    storage.set(model_name, pickle.dumps(model))

def stop_models(e=None):
    models = g.pop('models', None)

    if models is not None:
        # stoping models
        pass