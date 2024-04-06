"""
Receiver Application Module

This module defines endpoints for receiving and processing traffic events and incident reports.
"""

import json
import logging
import logging.config
import uuid
from datetime import datetime

import connexion
from connexion import NoContent
from pykafka import KafkaClient
import yaml

MAX_EVENTS = 5
EVENT_FILE = 'events.json'


with open('app_conf.yml', 'r', encoding='utf-8') as f:
    app_config = yaml.safe_load(f.read())


with open('log_conf.yml', 'r', encoding='utf-8') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Initialize KafkaClient on startup
client = None
topic = None

def connect_to_kafka():
    """ Connect to Kafka and return the client and topic """
    global client, topic
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

# Retry logic for connecting to Kafka
def retry_connect_to_kafka():
    """ retry Connection to Kafka """
    max_retries = 3  # Maximum number of retries
    current_retry = 0
    while current_retry < max_retries:
        try:
            connect_to_kafka()
            logger.info("Connected to Kafka")
            return True
        except Exception as e:
            logger.error("Error connecting to Kafka: %s", e)
            logger.info("Retrying connection to Kafka (%d/%d)", current_retry + 1, max_retries)
            
            current_retry += 1
            time.sleep(5)  # Wait for a few seconds before retrying
    logger.error("Failed to connect to Kafka after multiple attempts")
    return False

# Initial connection to Kafka
retry_connect_to_kafka()

def generate_trace_id():
    """Generate a unique trace ID."""
    return str(uuid.uuid4())


def recordTrafficFlow(body):
    """Record traffic flow event."""
    trace_id = generate_trace_id()
    logger.info("Received event traffic request with a trace id of %s", trace_id)

    body['trace_id'] = trace_id

    # client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
    # topic = client.topics[str.encode(app_config['events']['topic'])]
    producer = topic.get_sync_producer()
    msg = {
        "type": "TrafficFlow", 
        "datetime" : datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), 
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info("Returned event traffic response (Id: %s) with status 201", trace_id)
    return NoContent, 201


def reportIncident(body):
    """Report incident event."""
    trace_id = generate_trace_id()
    logger.info("Received event %s request with a trace id of %s", app_config['accident'], trace_id)

    body['trace_id'] = trace_id

    # client = KafkaClient(hosts='acit3855-kafla.eastus2.cloudapp.azure.com:9092')
    # topic = client.topics[str.encode('events')]
    producer = topic.get_sync_producer()
    msg = {
        "type": "reportIncident", 
        "datetime" : datetime.now().strftime("%Y-%m-%dT%H:%M:%S"), 
        "payload": body
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info("Returned event %s response (Id: %s) with status 201",
                app_config['accident'], trace_id)
    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("trafficreport.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080)
