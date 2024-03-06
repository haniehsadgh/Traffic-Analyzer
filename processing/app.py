import time
from datetime import datetime 
import json
import connexion
from connexion import NoContent
from flask import Flask, request, jsonify
from os import path
import db
# import processing.db as db
import yaml
import logging
import logging.config
from models import Stats
import requests
from apscheduler.schedulers.background import BackgroundScheduler



with open('app_conf.yml', 'r') as f:
 app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r') as f:
 log_config = yaml.safe_load(f.read())
 logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')


def populate_state():
    session = db.make_session()
    logger.info("Predict processing has started")
    latest_state = session.query(Stats).order_by(Stats.last_updated.desc()).first()
    print("latest state:", latest_state)
    logger.debug(f"latest state: {latest_state}")

    if latest_state is None:
        logger.info("No statics value. Initializing with default values.")
        latest_state = Stats(max_vehicle_count=0,
                    num_traffic_report=0,
                    num_incident_report=0,
                    last_updated=datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"))
       
    else:
       logger.debug("Latest statistics: %s" % latest_state)
    session.close()


    url = app_config["eventstore"]["url"]
    current_datetime_obj = datetime.now()
    current_datetime = current_datetime_obj.strftime("%Y-%m-%d %H:%M:%S.%f")
    traffic_report_response = requests.get(f"{app_config['eventstore']['url']}/traffic-flow", 
                                           params={"start_timestamp": latest_state.last_updated,
                                                "end_timestamp": current_datetime})
    
    incident_report_response = requests.get(f"{app_config['eventstore']['url']}/incident", 
                                           params={"start_timestamp": latest_state.last_updated,
                                                "end_timestamp": current_datetime})
    
    logger.info(f"Received {len(traffic_report_response.json())} traffic info events")
    logger.info(f"Received {len(incident_report_response.json())} incident events")
    
    if traffic_report_response.status_code != 200 or incident_report_response.status_code != 200:
        logger.error("Failed to fetch events from Data Store Service")
        # return

    traffic_report_res_json = traffic_report_response.json()
    incident_report_res_json = incident_report_response.json()
    logger.debug(traffic_report_res_json)
    logger.debug(incident_report_res_json)

    num_traffic_report = latest_state.num_traffic_report
    num_incident_report = latest_state.num_incident_report
    num_traffic_report += len(traffic_report_res_json)
    num_incident_report += len(incident_report_res_json)
    max_vehicle_count = latest_state.max_vehicle_count

    for report in traffic_report_res_json:
       if report["vehicleCount"] > latest_state.max_vehicle_count:
          max_vehicle_count = report["vehicleCount"]
          logger.debug(f"Processing traffic report for vehicle count with trace_id: {report['trace_id']}")



    new_stats = Stats(num_traffic_report=num_traffic_report,
                    num_incident_report=num_incident_report,
                    max_vehicle_count=max_vehicle_count,
                    last_updated=current_datetime_obj)
    session = db.make_session()
    session.add(new_stats)
    session.commit()
    session.close()
    logger.info("Prediction processing has ended")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_state, 
                    'interval',
                    seconds=app_config['scheduler']['period_sec'])
    sched.start()

def get_stats():
    logger.info("Request for statistics started")

    session = db.make_session()
    latest_stats = session.query(Stats).order_by(Stats.last_updated.desc()).first()

    if not latest_stats:
        logger.error("Statistics do not exist")
        session.close()
        return NoContent, 404

    stats_dict = latest_stats.to_dict()

    logger.debug("Current statistics: %s" % stats_dict)
    logger.info("Request for statistics completed")
    session.close()

    return stats_dict, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("trafficreport.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)

