import sys
import os
from flask import g, current_app
from models import models_info, models_classes

def get_models_info():
    if 'model_info' not in g:
        g.models_info = models_info

    return g.models_info

def get_models():
    if 'models' not in g:
        g.models = models_classes
    return g.models

def stop_models(e=None):
    models = g.pop('models', None)

    if models is not None:
        # stoping models
        pass