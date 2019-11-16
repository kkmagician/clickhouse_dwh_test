import logging
import requests

from airflow import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO, format="[%(levelname)s] %(asctime)s: %(message)s"
)

default_args = {
    "owner": "Airflow",
    "depends_on_past": False,
    "start_date": datetime(2019, 11, 15),
    "retries": 0,
}

# Using Docker secrets here
CH_USER = open("/run/secrets/UCHI_CH_USER").read()
CH_PASS = open("/run/secrets/UCHI_CH_PASS").read()

# Docker Swarm local network
CH_HOST = "http://uchich:8123"
CH_HOST_BASH = CH_HOST + f"/?user={CH_USER}&password={CH_PASS}"

# Vars
today = datetime.today().strftime("%Y%m%d")
file_location = "/usr/local/ch/event_data.json"


dag = DAG(
    "ch_file_insert", default_args=default_args, schedule_interval="30 6 * * *"
)

def run_query(q):
    resp = requests.post(CH_HOST, params={"user": CH_USER, "password": CH_PASS}, data=q)
    
    if resp.status_code == 200:
        return resp.text
    else:
        raise ValueError(resp.text)


def create_temp_table():
    """"""
    create_temp_table_sql = open("dags/ch_file_insert_sql/temp_table.sql").read().format(date=today)
    run_query(create_temp_table_sql)


push_table_script = \
    f'cat {file_location} | curl "{CH_HOST_BASH}&query=INSERT+INTO+raw.event_data_{today}+FORMAT+JSONEachRow" --data-binary @-'


def temp_to_prod():
    """"""
    temp_to_prod_sql = open("dags/ch_file_insert_sql/temp_to_prod.sql").read().format(date=today)
    result = run_query(temp_to_prod_sql)
    logging.info(result)


create_temp = PythonOperator(task_id="create_temp_table", python_callable=create_temp_table, dag=dag)
push_temp = BashOperator(task_id="push_temp_table", bash_command=push_table_script, dag=dag)
prod = PythonOperator(task_id="temp_to_prod", python_callable=temp_to_prod, dag=dag)

create_temp >> push_temp >> prod
