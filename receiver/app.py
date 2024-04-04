import time
from datetime import datetime 
import json
import connexion
from connexion import NoContent
from flask import Flask, request, jsonify
import requests
from os import path
import yaml
import logging
import uuid
import logging.config
from pykafka import KafkaClient

MAX_EVENTS = 5
EVENT_FILE = 'events.json'

with open('app_conf.yml', 'r') as f:
 app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f:
 log_config = yaml.safe_load(f.read())
 logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

def generate_trace_id():
    return str(uuid.uuid4())



def recordTrafficFlow(body):
    trace_id = generate_trace_id()
    logger.info(f"Recieved event traffic request with a trace id of {trace_id})")

    body['trace_id'] = trace_id

    client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()
    msg = { "type": "TrafficFlow", 
            "datetime" : 
                datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"), 
            "payload": body }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))


    logger.info(f"Returned event traffic response (Id: {trace_id}) with status 201")
    return NoContent, 201

    

def reportIncident(body):
    trace_id = generate_trace_id()
    logger.info(f"Recieved event {app_config['accident']} request with a trace id of {trace_id})")


    body['trace_id'] = trace_id

    client = KafkaClient(hosts='acit3855-kafla.eastus2.cloudapp.azure.com:9092')
    topic = client.topics[str.encode('events')]
    producer = topic.get_sync_producer()
    msg = { "type": "reportIncident", 
            "datetime" : 
                datetime.now().strftime(
                    "%Y-%m-%dT%H:%M:%S"), 
            "payload": body }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    

    logger.info(f"Returned event {app_config['accident']} response (Id: {trace_id}) with status 201")
    return NoContent, 201



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("trafficreport.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)

