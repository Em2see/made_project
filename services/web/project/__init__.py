from flask import Flask, render_template, send_from_directory
import os
import uuid
import numpy as np
from copy import copy
from .getter import getter
from .viewer import viewer
from .runner import runner
from .db import close_db
import logging

def_path = os.path.abspath("./")
view_path = os.path.join(def_path, "view")

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
## config

app.config['SECRET_KEY'] = 'secret!'

app.config['DATABASE'] = {
    'user': "smartcapex",
    'password': "1234",
    'host': "postgres",
    'port': "5432",
    'database': "smartcapex"
}

app.config['ENGINE'] = "postgresql+psycopg2://smartcapex:1234@/smartcapex?host=postgres:5432"

app.config['PATHS'] = {
    "def_path": def_path,
    "view_path": os.path.join(def_path, "view"),
    "static_path": os.path.join(view_path, "static"),
    "images_path": os.path.join(view_path, "imgs"),
    "fonts_path": os.path.join(view_path, "static", "themes/default/assets/fonts")
}

app.config['REDIS_MODELS'] = {
    'host': 'redis_host', 
    'port': 6379,
    'db': 1
}

app.register_blueprint(getter)
app.register_blueprint(viewer)
app.register_blueprint(runner)


@app.teardown_appcontext
def teardown_df(exception):
    close_db()

__all__ = ['app']