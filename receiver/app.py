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


# def write_data(type, req):
#     if not path.isfile(EVENT_FILE):
#         with open(EVENT_FILE, "w") as file:
#             file.write('[]')

#     file_content = []
#     if path.isfile(EVENT_FILE):
#         with open(EVENT_FILE, "r") as read_file:
#             try:
#                 file_content = json.load(read_file)
#             except json.JSONDecodeError:
#                 print("Error decoding JSON. Initializing with an empty list.")
#                 file_content = []

#     request_key = f"num_{type.lower()}"
#     recent_key = f"recent_{type.lower()}"

#     file_content_dict = dict(file_content)

#     file_content_dict.setdefault(request_key, 0)
#     file_content_dict.setdefault(recent_key, [])

#     file_content_dict[request_key] += 1
#     # file_content_dict[recent_key].append(req)
#     file_content_dict[recent_key].insert(0, req)
#     file_content_dict[recent_key] = file_content_dict[recent_key][:MAX_EVENTS]
    
#     with open(EVENT_FILE, "w") as write_file:
#         json.dump(file_content_dict, write_file, indent='\t')


def recordTrafficFlow(body):
    trace_id = generate_trace_id()
    logger.info(f"Recieved event traffic request with a trace id of {trace_id})")
    

    # msg = {
    #     "msg_data": f"{body['traffic_id']}, aircraft ID: {body['intersectionId']}, recorded {body['dateRecorded']} vehicle count: {body['vehicleCount']}",
    #     "received_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
    # }
    body['trace_id'] = trace_id
    # req = requests.post(app_config['traffic_condition']['url'], json=body, headers={'Content-Type': 'application/json'})
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

    # write_data("Traffic Flow", msg)
    # return NoContent, 201
    logger.info(f"Returned event traffic response (Id: {trace_id}) with status 201")
    return NoContent, 201

    

def reportIncident(body):
    trace_id = generate_trace_id()
    logger.info(f"Recieved event {app_config['accident']} request with a trace id of {trace_id})")

    # msg = {
    #     "msg_data": f"Confirmation incident for {body['id']}. Your camera ID: {body['cameraId']}",
    #     "received_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
    # }
    body['trace_id'] = trace_id
    #req = requests.post(app_config['accident']['url'], json=body, headers={'Content-Type': 'application/json'})
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
    
    # write_data("Incident report", msg)
    # return NoContent, 201
    logger.info(f"Returned event {app_config['accident']} response (Id: {trace_id}) with status 201")
    return NoContent, 201



app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("trafficreport.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)

