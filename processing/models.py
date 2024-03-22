from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy import Integer, String, DateTime, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Stats(Base):
    __tablename__ = 'stats'

    id = mapped_column(Integer, primary_key=True)
    num_traffic_report = mapped_column(Integer, nullable=False)
    num_incident_report = mapped_column(Integer, nullable=False)
    max_vehicle_count = mapped_column(Integer, nullable=False)
    last_updated = mapped_column(DateTime, nullable=False, default=func.now())


    # def __init__(self, num_traffic_report, num_incident_report, max_vehicle_count, last_updated):
    #     """ Initializes a blood pressure reading """
    #     self.num_traffic_report = num_traffic_report
    #     self.num_incident_report = num_incident_report
    #     self.max_vehicle_count = max_vehicle_count
    #     self.last_updated = last_updated

    def to_dict(self):
        """ Dictionary Representation of statics reading """
        dict = {}
        dict['id'] = self.id
        dict['num_traffic_report'] = self.num_traffic_report
        dict['num_incident_report'] = self.num_incident_report
        dict['max_vehicle_count'] = self.max_vehicle_count
        dict['last_updated'] = self.last_updated.strftime("%Y-%m-%dT%H:%M:%S.%f")
            
        return dict