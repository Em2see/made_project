from flask import Blueprint, url_for, make_response, send_from_directory
from flask import jsonify, send_file, request, g, render_template, current_app
from .db import get_db, getArray, getDict
from .models import get_models_info
import os
import uuid

viewer = Blueprint('viewer', __name__, template_folder='../view')
viewer.config = {}
viewer.logger = None
viewer.paths = {}

defaults = {
    "radius": 300,
    "size": 50,
    "tech": 5
}

pointColumns = {
    'x': "X",
    'y': "Y",
    'tech': "Technology",
    'cap': "Capacity",
    'height': "Height",
    'azimuth': "Azimuth",
    'date_start': "Start Date",
    'date_end': "End Date"
}

@viewer.record
def record_params(setup_state):
  app = setup_state.app
  viewer.config = {key:value for key,value in app.config.items()}
  app.logger.info(str(viewer.config))
  viewer.logger = app.logger
  viewer.paths = viewer.config['PATHS']

@viewer.route('/', methods=['GET'])
def index():
    return render_template('vis.html', defaults=defaults)
    
@viewer.route('/table', methods=['GET'])
def table():
    cursor = get_db().cursor()
    sql_select_query = "SELECT * FROM points"
    cursor.execute(sql_select_query)
    points = cursor.fetchall()
    column_names = [pointColumns[desc[0]] for desc in cursor.description if desc[0] not in ['id']]

    return render_template('table.html', points=points, column_names=column_names)

@viewer.route('/models_info', methods=['GET'])
def models_info():
    models_info = get_models_info()
    return render_template('models_info.html', models_info=models_info)

@viewer.route('/models_status', methods=['GET'])
def models_status():
    models_info = get_models_info()
    
    models_data, cols = getArray("SELECT tr.model_name, tr.start, tr.stop, ts.start, ts.stop FROM train_run tr INNER JOIN test_run ts ON ts.model_name = tr.model_name")

    m_names = [i for i in models_info.keys()]

    models_data = {m[0]:m[1:] for m in models_data}

    return render_template('models_status.html', models_info=models_info, models_data=models_data)

@viewer.route('/bsgraph', methods=['GET'])
def bs_graph():
    models_info = get_models_info()
    
    bs_ids, _ = getArray("SELECT DISTINCT id FROM ((SELECT id FROM train) UNION (SELECT id FROM test)) AS ids")

    bs_ids = [i[0] for i in bs_ids]

    return render_template('bs_graph.html', models_info=models_info, bs_ids=bs_ids)

@viewer.route('/static/<filename>', methods=['GET'])
def staticfile(filename):
    return send_file(os.path.join(viewer.paths['static_path'], filename))
    
@viewer.route('/static/themes/default/assets/fonts/<filename>', methods=['GET'])
def fonts(filename):
    return send_file(os.path.join(viewer.paths['fonts_path'], filename))
    
@viewer.route('/static/images/<filename>', methods=['GET'])
def images(filename):
    viewer.logger.info("images %s" % str(defaults))
    return send_file(os.path.join(viewer.paths['images_path'], filename))
    
@viewer.route('/view/<path:filename>', methods=['GET'])
def pages(filename):
    viewer.logger.info("view %s" % filename)
    return send_file(os.path.join(viewer.paths['view_path'], filename))

@viewer.route('/update_params', methods=['POST'])
def update_params():
    params = request.get_json()
    for k, v in params.items():
        defaults[k] = v
    return make_response(jsonify({}), 200)

@viewer.route('/table/add', methods=['POST'])
def addNewPoint():
    point = request.get_json()
    viewer.logger.info("view %s" % str(point))
    id_ = uuid.uuid4()
    points.loc[id_] = pd.Series(point)
    return make_response(jsonify({"id": id_}), 200)
    
@viewer.route('/table/<point_id>', methods=['DELETE'])
def removePoint(point_id):
    try:
        points.drop(labels=[point_id], axis=0, inplace=True)
        resp = make_response(jsonify({}), 200)
    except KeyError as ex:
        resp = make_response(jsonify({}), 404)
        
    return resp

@viewer.route('/table/get', methods=['GET'])
def getAllAddedPoints():
    cursor = get_db().cursor()
    sql_select_query = """SELECT * FROM points"""
    cursor.execute(sql_select_query)
    records = cursor.fetchall()
    return make_response(jsonify(records), 200)

@viewer.route('/vis/antenna', methods=['GET'])
def getAntennaDiagram():
    #params = request.get_json()
    #params['diagram_type'] = 'antennas'
    #run_pred(params)
    #return send_file(antennas_path, mimetype='image/png')
    pass

@viewer.route('/vis/heatmap', methods=['GET'])
def getHeatMapDiagram():
    #params = request.get_json()
    #params['diagram_type'] = 'heatmap'
    #run_pred(params)
    #return send_file(heatmap_path, mimetype='image/png')
    pass
