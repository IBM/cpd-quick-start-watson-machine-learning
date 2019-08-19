import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2 import sql
import logging
import sys
from config.postgres import config
import time
import datetime
import pandas as pd
import os.path

TABLE_NAME = "reefer_container_events"
DATA_GENERATION_INTERVAL = 5

columns = []


def create_table_command():
  return (f"""
        CREATE TABLE {TABLE_NAME} (
                timestamp TIMESTAMP,
                id INTEGER,
                temperature DECIMAL,
                target_temperature DECIMAL,
                amp DECIMAL,
                cumulative_power_consumption DECIMAL,
                content_type INTEGER,
                humidity DECIMAL,
                co2 DECIMAL,
                door_open INTEGER,
                maintainence_required INTEGER,
                defrost_cycle INTEGER
        )
        """)


def insert_event(cur, columns, values):
    insert_statement = sql.SQL("insert into {} ({}) values ({})").format(
            sql.Identifier(TABLE_NAME),
            sql.SQL(', ').join(map(sql.Identifier, columns)),
                sql.SQL(', ').join(sql.Placeholder() * len(values)))
    logging.debug(values)
    cur.execute(insert_statement, values)


def connect_to_db():
    # read connection parameters
    params = config()
    # connect to the PostgreSQL server
    logging.info('Connecting to PostgreSQL...')
    conn = psycopg2.connect(**params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    return conn


def create_table(cur):
    # Create the reefer container event table
    try:
        cur.execute(create_table_command())
    except psycopg2.errors.DuplicateTable as err:
        logging.info(err) # table already created
    except Exception as err:
        logging.error(err)


def load_events_data():
    df = pd.read_csv(os.path.join('data', 'data.csv'), delimiter=",")
    columns.extend(df.columns.values)
    return df.values


def setup_logger():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    root.addHandler(handler)


def main():
    setup_logger()
    conn = None
    cur = None
    try:
        conn = connect_to_db()
        cur = conn.cursor()
        create_table(cur)
        logging.info("starting to produce data...")
        events = load_events_data()
        while True:
            for event in events:
                sleep = DATA_GENERATION_INTERVAL
                try:
                    event[columns.index("timestamp")] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    insert_event(cur, columns, event)
                except Exception as err:
                    logging.error(err)
                    sleep = DATA_GENERATION_INTERVAL # Longer sleep before retrying
                time.sleep(sleep)
    except Exception as err:
        logging.info(err)
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
            logging.info('Database connection closed.')


if __name__ == '__main__':
    main()
