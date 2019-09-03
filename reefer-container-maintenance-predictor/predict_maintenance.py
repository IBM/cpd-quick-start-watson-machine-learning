import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import DictCursor
from psycopg2 import sql
import logging
from config.postgres import config
from config.mongodb import mongo_config
import datetime
import time
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
from watson_machine_learning_client import WatsonMachineLearningAPIClient
import pickle
from pymongo import MongoClient
import decimal
from flask import Flask, render_template, jsonify, request
import atexit
from apscheduler.schedulers.background import BackgroundScheduler


TABLE_NAME = "reefer_container_events"
CHECK_FOR_EVENTS_INTERVAL = 2

app = Flask(__name__)
mongo_connection = None
postgres_connection = None
postgres_connection_cursor = None
scoring_url = None
cpd_access_token = None
last_timestamp_event = datetime.datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S')  # epoch


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getScoringResult')
def get_scoring_result():
    if mongo_connection is None:
        return jsonify({"results": []})

    timestamp_param = request.args.get('timestamp')
    if timestamp_param is None:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.fromtimestamp(int(timestamp_param) / 1000)  # timestamp param in milliseconds

    greatest_timestamp = get_datetime_millis(date)
    results = []
    try:
        for doc in mongo_connection.find({"date": {"$gt": date}}).sort("date"):
            cur_doc_timestamp = get_datetime_millis(doc["date"])
            results.append({
                "id": doc["id"],
                "temperature": doc["temperature"],
                "cumulative_power_consumption": doc["cumulative_power_consumption"],
                "humidity": doc["humidity"],
                "maintenance_required": doc["maintenance_required"],
                "timestamp": cur_doc_timestamp
            })
            if cur_doc_timestamp > greatest_timestamp:
                greatest_timestamp = cur_doc_timestamp
    except Exception as e:
        print(e)

    return jsonify({"results": results, "timestamp": greatest_timestamp})

def get_datetime_millis(dt):
    return int(dt.timestamp() * 1000.0)

def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)

def connect_to_mongo_db():
    global mongo_connection
    logging.info('Connecting to MONGODB ' + mongo_config()['connection_string'])
    mongo_client = MongoClient(mongo_config()['connection_string'])
    db = mongo_client[mongo_config()['database']]
    mongo_connection = db['container_maintenance_predictions']


def connect_to_postgres_db():
    global postgres_connection
    global postgres_connection_cursor
    # read connection parameters
    params = config()
    # connect to the PostgreSQL server
    logging.info('Connecting to PostgreSQL...')
    postgres_connection = psycopg2.connect(**params)
    postgres_connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    postgres_connection_cursor = postgres_connection.cursor(cursor_factory=DictCursor)


def get_cpd_config():
    wml_url = os.getenv('ICP4D_CLUSTER_HOST', False)
    if not wml_url:
        sys.exit('missing ICP4D_CLUSTER_HOST env var')
        return

    wml_port = os.getenv('ICP4D_CLUSTER_PORT', False)
    if not wml_port:
        sys.exit('missing ICP4D_CLUSTER_PORT env var')
        return

    wml_user = os.getenv('ICP4D_CLUSTER_USER', False)
    if not wml_user:
        sys.exit('missing ICP4D_CLUSTER_USER env var')
        return

    wml_password = os.getenv('ICP4D_CLUSTER_PASSWORD', False)
    if not wml_password:
        sys.exit('missing ICP4D_CLUSTER_PASSWORD env var')
        return

    return {"url": wml_url, "port": wml_port, "user": wml_user, "password": wml_password}


def get_cpd_access_token(cpd_config):
    auto_request = requests.get(f"https://{cpd_config['url']}:{cpd_config['port']}/v1/preauth/validateAuth",
                                auth=(cpd_config['user'], cpd_config['password']), verify=False)
    return auto_request.json()['accessToken']


def get_events():
    fld_list = ['timestamp', 'id', 'temperature', 'cumulative_power_consumption', 'humidity']
    placeholder_str = sql.SQL("SELECT {} FROM {} WHERE timestamp > {}").format(
        sql.SQL(",").join(map(sql.Identifier, fld_list)),
        sql.Identifier(TABLE_NAME),
        sql.Placeholder()
    )
    postgres_connection_cursor.execute(placeholder_str, [last_timestamp_event])
    return postgres_connection_cursor.fetchall()


def connect_to_wml():
    wml_url = os.getenv('ICP4D_CLUSTER_HOST', False)
    if not wml_url:
        sys.exit('missing ICP4D_CLUSTER_HOST env var')
        return

    wml_port = os.getenv('ICP4D_CLUSTER_PORT', False)
    if not wml_port:
        sys.exit('missing ICP4D_CLUSTER_PORT env var')
        return

    wml_user = os.getenv('ICP4D_CLUSTER_USER', False)
    if not wml_user:
        sys.exit('missing ICP4D_CLUSTER_USER env var')
        return

    wml_password = os.getenv('ICP4D_CLUSTER_PASSWORD', False)
    if not wml_password:
        sys.exit('missing ICP4D_CLUSTER_PASSWORD env var')
        return

    wml_credentials = {
        "url": f"https://{wml_url}",
        "username": f"{wml_user}",
        "password": f"{wml_password}",
        "instance_id": "icp"
    }
    return WatsonMachineLearningAPIClient(wml_credentials)


def store_model_in_wml(wml_client):
    with open(os.path.join(os.path.dirname( __file__ ), 'model', "model.pkl"), 'rb') as pickle_file:
        loaded_model = pickle.load(pickle_file)
    model_props = {wml_client.repository.ModelMetaNames.NAME: "reefer_malfunction_prediction",
                   wml_client.repository.FunctionMetaNames.TAGS:
                       [{"value": "reefer_malfunction_prediction",
                        "description": "Predicting malfunction in reefer containers"}]}
    return wml_client.repository.store_model(loaded_model, model_props)


def get_scoring_url(wml_client, model_details):
    model_uid = wml_client.repository.get_model_uid(model_details)
    deployment_details = wml_client.deployments.create(model_uid, "reefer container maintenance model deployment")
    return wml_client.deployments.get_scoring_url(deployment_details)


def predict():
    global last_timestamp_event
    try:
        headers = {"Authorization": "Bearer " + cpd_access_token}
        feature_cols = ['temperature', 'cumulative_power_consumption', 'humidity']
        results = get_events()
        if postgres_connection_cursor.rowcount > 0:
            for row in results:
                values = [str(row[k]) for k in feature_cols]
                scoring_payload = {'fields': feature_cols, 'values': [values]}
                online_scoring_request = requests.post(
                    scoring_url, headers=headers, verify=False, json=scoring_payload)
                prediction = online_scoring_request.json()
                prediction_row = {'id': row['id'],
                                  'temperature': str(row['temperature']),
                                  'cumulative_power_consumption': str(row['cumulative_power_consumption']),
                                  'humidity': str(row['humidity']),
                                  'maintenance_required': prediction['values'][0][0],
                                  "date": datetime.datetime.now()}
                decimal.Decimal('10.0')
                mongo_connection.insert_one(prediction_row)
                logging.debug(prediction_row)
                last_timestamp_event = results[postgres_connection_cursor.rowcount - 1][0]
    except Exception as err:
        logging.error(err)


def on_shutdown():
    if postgres_connection_cursor is not None:
        postgres_connection_cursor.close()
    if postgres_connection is not None:
        postgres_connection.close()
        logging.info('Database connection closed.')


def set_cpd_access_token():
    global cpd_access_token
    cpd_config = get_cpd_config()
    logging.info('Obtaining CPD Access token...')
    cpd_access_token = get_cpd_access_token(cpd_config)


def set_wml_scoring_url():
    global scoring_url
    logging.info('Connecting to WML...')
    wml_client = connect_to_wml()
    logging.info('Persisting model to WML...')
    model_details = store_model_in_wml(wml_client)
    logging.info('Obtaining scoring url...')
    scoring_url = get_scoring_url(wml_client, model_details)


def set_prediction_job():
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=predict, trigger="interval", seconds=CHECK_FOR_EVENTS_INTERVAL)
    scheduler.start()
    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())


def make_connections():
    connect_to_mongo_db()
    connect_to_postgres_db()


def main():
    setup_logger()
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    make_connections()
    set_cpd_access_token()
    set_wml_scoring_url()
    set_prediction_job()
    atexit.register(on_shutdown)


if __name__ == '__main__':
    main()
    app.run(host='0.0.0.0', port=8080)
