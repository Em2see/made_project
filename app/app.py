from flask import Flask, request, jsonify
import psycopg2
import pandas as pd
import datetime

# declare constants
HOST = '0.0.0.0'
PORT = 8888

# initialize flask application
app = Flask(__name__)
connection = psycopg2.connect(user="smartcapex",password="1234",host="127.0.0.1",port="5432",database="smartcapex")


@app.route('/')
def home():
    return jsonify({'Ooops'})

@app.route('/get_id/simple/<id>', methods=['GET','POST'])
def simple_id(id):
    cursor = connection.cursor()
    sql_select_query = """select * from test_pred_simple where id = %s"""
    cursor.execute(sql_select_query, (id, ))
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200

@app.route('/get_date/simple/<date>', methods=['GET','POST'])
def simple_date(date):
    cursor = connection.cursor()
    sql_select_query = """select * from test_pred_simple where date_ = %s"""
    cursor.execute(sql_select_query, (id, ))
    record = cursor.fetchall()
    if len(record) == 0:
        return jsonify({}), 404
    return jsonify(record), 200


if __name__ == '__main__':
    # run web server
    app.run(host=HOST,
            debug=False,  # automatic reloading enabled
            port=PORT)
