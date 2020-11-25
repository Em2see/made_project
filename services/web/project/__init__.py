from flask import Flask, render_template, send_from_directory
import os
import uuid
import numpy as np
from copy import copy
from .getter import getter
from .viewer import viewer
from .db import close_db

def_path = os.path.abspath("./")
view_path = os.path.join(def_path, "view")

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.register_blueprint(getter, __name__)
app.register_blueprint(viewer, __name__, template_folder=view_path)

## config

app.config['SECRET_KEY'] = 'secret!'

app.config['DATABASE'] = {
    'user': "smartcapex",
    'password': "1234",
    'host': "127.0.0.1",
    'port': "5432",
    'database': "smartcapex"
}

app.config['PATHS'] = {
    "def_path": def_path,
    "view_path": os.path.join(def_path, "view"),
    "static_path": os.path.join(view_path, "static"),
    "images_path": os.path.join(view_path, "imgs"),
    "fonts_path": os.path.join(view_path, "static", "themes/default/assets/fonts")
}


@app.teardown_appcontext
def teardown_df(exception):
    close_db()

