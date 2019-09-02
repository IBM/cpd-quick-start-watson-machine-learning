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
from bson.decimal128 import Decimal128

TABLE_NAME = "reefer_container_events"
CHECK_FOR_EVENTS_INTERVAL = 2


def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    if not root.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        root.addHandler(handler)


def connect_to_mongo_db():
    logging.info('Connecting to MONGODB ' + mongo_config()['connection_string'])
    mongo_client = MongoClient(mongo_config()['connection_string'])
    db = mongo_client[mongo_config()['database']]
    predictions = db['container_maintenance_predictions']
    return predictions


def connect_to_postgres_db():
    # read connection parameters
    params = config()
    # connect to the PostgreSQL server
    logging.info('Connecting to PostgreSQL...')
    conn = psycopg2.connect(**params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


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


def get_events(cur, last_timestamp_event):
    fld_list = ['timestamp', 'id', 'temperature', 'cumulative_power_consumption', 'humidity']
    placeholder_str = sql.SQL("SELECT {} FROM {} WHERE timestamp > {}").format(
        sql.SQL(",").join(map(sql.Identifier, fld_list)),
        sql.Identifier(TABLE_NAME),
        sql.Placeholder()
    )
    cur.execute(placeholder_str, [last_timestamp_event])
    return cur.fetchall()


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


def main():
    setup_logger()
    conn = None
    cur = None
    try:
        client = connect_to_mongo_db()
        db = client[mongo_config()['database']]
        print("database name " + db.name)
        predictions = db['reefer_container_predictions']
        id = '1234'
        prediction_row = {'id': id,
                          'maintenance_required': 'true'}
        predictions.insert_one(prediction_row)
        details = predictions.find_one({'id': id})
        logging.debug(details)

        conn = connect_to_postgres_db()
        cur = conn.cursor(cursor_factory=DictCursor)
        cpd_config = get_cpd_config()
        logging.info('Obtaining WML Access token...')
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        cpd_access_token = get_cpd_access_token(cpd_config)
        logging.info('Connecting to WML...')
        wml_client = connect_to_wml()
        logging.info('Persisting model to WML...')
        model_details = store_model_in_wml(wml_client)
        logging.info('Obtaining scoring url...')
        scoring_url = get_scoring_url(wml_client, model_details)
        last_timestamp_event = datetime.datetime(1970, 1, 1).strftime('%Y-%m-%d %H:%M:%S')  # epoch

        headers = {"Authorization": "Bearer " + cpd_access_token}
        feature_cols = ['temperature', 'cumulative_power_consumption', 'humidity']

        while True:
            logging.debug("quering postgres for events")
            results = get_events(cur, last_timestamp_event)
            logging.debug("got results")
            if cur.rowcount > 0:
                for row in results:
                    values = [str(row[k]) for k in feature_cols]
                    scoring_payload = {'fields': feature_cols, 'values': [values]}
                    online_scoring_request = requests.post(
                        scoring_url, headers=headers, verify=False, json=scoring_payload)
                    prediction = online_scoring_request.json()
                    logging.debug("simple insert!")
                    prediction_row = {'id': id,
                                      'maintenance_required': 'true'}
                    predictions.insert_one(prediction_row)
                    logging.debug("simple insert works!")
                    prediction_row = {'id': row['id'],
                                      'maintenance_required': prediction['values'][0][0]}
                    predictions = connect_to_mongo_db() # issue on cluster reconnect
                    logging.debug(predictions)
                    predictions.insert_one(prediction_row)
                    logging.debug(prediction_row)
                    last_timestamp_event = results[cur.rowcount - 1][0]
            time.sleep(CHECK_FOR_EVENTS_INTERVAL)
    except Exception as err:
        logging.error(err)
    finally:
        if cur is not None:
            cur.close() 
        if conn is not None:
            conn.close()
            logging.info('Database connection closed.')


if __name__ == '__main__':
    main()
