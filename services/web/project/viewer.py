from flask import Blueprint, url_for, make_response, send_from_directory
from flask import jsonify, send_file, request, g, render_template, current_app
from . import db
import os
import uuid

viewer = Blueprint('viewer', __name__)

defaults = {
    "radius": 300,
    "size": 50,
    "tech": 5
}

paths = current_app.config['PATHS']

@viewer.route('/', methods=['GET'])
def index():
    return render_template('vis.html', defaults=defaults)
    
@viewer.route('/table', methods=['GET'])
def table():
    return render_template('table.html', points=points)

@viewer.route('/static/<filename>', methods=['GET'])
def staticfile(filename):
    return send_file(os.path.join(paths['static_path'], filename))
    
@viewer.route('/static/themes/default/assets/fonts/<filename>', methods=['GET'])
def fonts(filename):
    return send_file(os.path.join(paths['fonts_path'], filename))
    
@viewer.route('/static/images/<filename>', methods=['GET'])
def images(filename):
    app.logger.info("images %s" % str(defaults))
    return send_file(os.path.join(paths['images_path'], filename))
    
@viewer.route('/view/<path:filename>', methods=['GET'])
def pages(filename):
    app.logger.info("view %s" % filename)
    return send_file(os.path.join(paths['view_path'], filename))

@viewer.route('/update_params', methods=['POST'])
def update_params():
    params = request.get_json()
    for k, v in params.items():
        defaults[k] = v
    return make_response(jsonify({}), 200)

@viewer.route('/table/add', methods=['POST'])
def addNewPoint():
    point = request.get_json()
    app.logger.info("view %s" % str(point))
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
    res = points.reset_index().to_json(orient='records')
    return make_response(res, 200)

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