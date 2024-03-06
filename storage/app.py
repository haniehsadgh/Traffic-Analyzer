import time
from datetime import datetime 
import json
import connexion
from connexion import NoContent
from flask import Flask, request, jsonify
from os import path
from models_mysql import TrafficFlow, IncidentReport, Base
import db_mysql 
import yaml
import logging
import logging.config
from sqlalchemy import and_



with open('app_conf.yml', 'r') as f:
 app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f:
 log_config = yaml.safe_load(f.read())
 logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

session = db_mysql.make_session()
def log_to_db(session, body, type):
    if type not in ("traffic", "incident"):
        raise  ValueError("Invalid event type: {}".format(type))
    
    if type == "traffic":
        new_event = TrafficFlow(
            trace_id=body["trace_id"],
            traffic_id=body["traffic_id"],
            intersection_id=body["intersectionId"],
            dateRecorded=body["dateRecorded"],
            vehicle_count=body["vehicleCount"]
        )
    else:
        new_event = IncidentReport(
            trace_id=body["trace_id"],
            accident_id=body["accident_id"],
            camera_id=body["cameraId"],
            timestamp=body["timestamp"],
            incidentType=body["incidentType"]
        )
    
    session.add(new_event)
    session.commit()
    session.close()

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
    log_to_db(session, body,"traffic")
    logger.debug(f"Recieved event traffic request with a trace id of {body['trace_id']})")
    return NoContent, 201


def reportIncident(body):
    log_to_db(session, body,"incident")
    logger.debug(f"Recieved event accident request with a trace id of {body['trace_id']})")
    return NoContent, 201


def get_traffic_report(start_timestamp, end_timestamp):
    session = db_mysql.make_session()
    start_timestamp_dt = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S.%f")
    end_timestamp_dt = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    results = session.query(TrafficFlow).filter(
        and_(TrafficFlow.date_created >= start_timestamp_dt,TrafficFlow.date_created < end_timestamp_dt))
    
    result_list = []
    for result in results:
       result_list.append(result.to_dict())

    session.close()
    logger.info("Query for Traffic report after %s returns %d results" % (start_timestamp, len(result_list)))

    return result_list, 200

def get_incident_report(start_timestamp, end_timestamp):
    session = db_mysql.make_session()
    start_timestamp_dt = datetime.strptime(start_timestamp, "%Y-%m-%d %H:%M:%S.%f")
    end_timestamp_dt = datetime.strptime(end_timestamp, "%Y-%m-%d %H:%M:%S.%f")

    results = session.query(IncidentReport).filter(
    and_(IncidentReport.date_created >= start_timestamp_dt,IncidentReport.date_created < end_timestamp_dt))
    
    result_list = []
    for result in results:
       result_list.append(result.to_dict())

    session.close()
    logger.info("Query for Incident report after %s returns %d results" % (start_timestamp, len(result_list)))

    return result_list, 200

# database_name = app_config['datastore']['database']
# port = app_config['datastore']['port']
# username = app_config['datastore']['user']
# password = app_config['datastore']['password']
# hostname =app_config['datastore']['hostname']

# logger.info(f"Connecting to {database_name}. Hostname:{hostname}, Port:{port}")

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("trafficreport.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8090)

