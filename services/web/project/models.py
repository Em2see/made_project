import sys
import os
from flask import g, current_app

models_path = os.path.abspath("/")
if models_path not in sys.path:
    sys.path.append(models_path)
    from models import ARMA_model, Boosting_model, Linear_model
    from models import models_info

def get_models_info():
    if 'model_info' not in g:
        g.models_info = models_info

    return g.models_info

def get_models():
    if 'models' not in g:
        g.models = {
            "arma": ARMA_model(),
            "boosting": Boosting_model(),
            "linear": Linear_model()
        }
    return g.models

def stop_models(e=None):
    models = g.pop('models', None)

    if models is not None:
        # stoping models
        pass