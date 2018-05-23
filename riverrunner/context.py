import datetime
from sqlalchemy import create_engine, select
from sqlalchemy.engine.url import URL
from sqlalchemy import Column, Integer, String, Float, DateTime, Index, ForeignKey, ForeignKeyConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

""" SQLAlchemy declarative base for ORM features """
Base = declarative_base()


class Context(object):
    """generate a managed session with the database

    Attributes:
        Session (sqlalchemy.orm.sessionmaker): managed connection to database. `see more <http://docs.sqlalchemy.org/en/latest/orm/session.html>`_.
    """

    def __init__(self, connection_string):
        """initialize the connection

        Args:
            connection_string (dict): must contain {drivername,host,port,username,paassword,database}
        """

        self.__engine = create_engine(URL(**connection_string))

        self.Session  = sessionmaker()
        self.Session.configure(bind=self.__engine)

        try:
            s = self.Session()
        except OperationalError:
            print("Unable to connect to destination db")
            exit(101)

        Base.metadata.create_all(self.__engine)


class Address(Base):
    """ORM mapping for addresses

    Attributes:
        address (str): street address limited to 255 characters
        city (str): city name limited to 255 characters
        county (str): county name limited to 255 characters
        latitude (float): geographical latitude in decimal date format (DD)
        longitude (float): geographical longit ude in decimal date format (DD)
        state (str): two character state identifier
        zip (str): zip code limited to 10 characters
    """
    __tablename__ = 'address'

    latitude  = Column(Float, primary_key=True)
    longitude = Column(Float, primary_key=True)

    address = Column(String(255))
    city    = Column(String(255))
    county  = Column(String(255))

    state   = Column(ForeignKey('state.short_name'))
    state_  = relationship('State')

    zip = Column(String(10))

    Index('idx_latlon', 'latitude', 'longitude', unique=True)

    def __repr__(self):
        return '<Address(latitude="%s", longitude="%s")>' % (self.latitude, self.longitude)

    def __str__(self):
        return '%s, %s, %s' % (self.address, self.city, self.state)


class Measurement(Base):
    """ORM mapping for measurements

    Attributes:
        date_time (DateTime): timestamp for when the measurement was taken
        metric_id (int): reference to the metric gathered
        station_id (str): reference to the weather station that gathered the measurement
        value (float): the value recorded
    """
    __tablename__ = 'measurement'

    date_time = Column(DateTime, primary_key=True)

    metric_id = Column(ForeignKey('metric.metric_id'), primary_key=True)
    metric    = relationship('Metric')

    station_id = Column(ForeignKey('station.station_id'), primary_key=True)
    station = relationship('Station')

    value = Column(Float)

    Index('idx_station', 'station_id')
    Index('idx_date_time', 'date_time')

    def __repr__(self):
        return f'<Measurement(station_id="{self.station_id}", datetime="{self.date_time}", metric="{self.metric_id}")>'

    def __str__(self):
        return 'station: %s, datetime: %s, metric: %s' % \
               (self.station_id, self.date_time, self.metric_id)

    @property
    def dict(self):
        """dictionary representation of the measurement"""
        return {
            'date_time': self.date_time,
            'metric_id': self.metric_id,
            'station_id': self.station_id,
            'source': self.station.source,
            'value': self.value
        }


class Metric(Base):
    """ORM mapping for metrics

    Attributes:
        metric_id (int): metric id
        description (str): a short description of the metric
        units (str): units the metric is gathered in
    """
    __tablename__ = 'metric'

    metric_id = Column(String(31), primary_key=True)

    description = Column(String(255))
    name  = Column(String(255))
    units = Column(String(31))

    def __repr__(self):
        return f'<Metric(metric_id="{self.metric_id}", name="{self.name}")>'

    def __str__(self):
        return f'metric_id: {self.metric_id}, name: {self.name}'


class Prediction(Base):
    """ORM mapping for predictions

    Attributes:
        run_id (int): reference to the river run this prediction is referencing
        timestamp (DateTime): timestamp for the prediction
        fr_lb (float): the lower bound of a confidence interval surrounding the prediction
        fr (float): the predicted flow rate
        fr_ub (float): the upper bound of a confidence interval surrounding the prediction
    """
    __tablename__ = 'prediction'

    run_id = Column(ForeignKey('river_run.run_id'), primary_key=True)
    timestamp = Column(DateTime, primary_key=True)

    fr_lb = Column(Float)
    fr    = Column(Float)
    fr_ub = Column(Float)

    @hybrid_property
    def year(self):
        return self.timestamp.year

    @hybrid_property
    def month(self):
        return self.timestamp.month

    @hybrid_property
    def day(self):
        return self.timestamp.day

    def __repr__(self):
        return '<Prediction(run_id="%s", datetime="%s")>' % (self.run_id, self.timestamp)

    def __str__(self):
        return 'run_id: %s, %s, lb: %s, fr: %s, ub: %s' % \
               (self.run_id, self.timestamp, self.fr_lb, self.fr, self.fr_ub)


class RiverRun(Base):
    """ORM mapping for a river run

    Attributes:
        run_id (int): id
        class_rating (str): the run's white-water class rating
        distance (float): the physical length of the run in miles
        max_level (int): maximum recommended flow rate
        min_level (int): minimum recommended flow rate
        put_in_latitude (float): geographical latitude in decimal degree format (DD) representing where the run begins
        put_in_longitude (float): geographical longitude (DD) representing where the run begins
        river_name (str): the name of the river
        run_name (str): the name of the run
        take_out_latitude (float) geographical latitude (DD) representing where the run ends
        take_out_longitude (float) geographical longitdue (DD) representing where the run ends
    """
    __tablename__ = 'river_run'

    __table_args__ = (
        ForeignKeyConstraint(
            ('put_in_latitude', 'put_in_longitude'),
            ('address.latitude', 'address.longitude')
        ),
        ForeignKeyConstraint(
            ('take_out_latitude', 'take_out_longitude'),
            ('address.latitude', 'address.longitude')
        )
    )

    run_id = Column(Integer, primary_key=True, index=True)

    class_rating = Column(String(31))
    max_level = Column(Integer)
    min_level = Column(Integer)

    predictions = relationship("Prediction", lazy='joined')

    put_in_latitude  = Column(Float, nullable=False)
    put_in_longitude = Column(Float, nullable=False)
    put_in_address = relationship(
        'Address',
        primaryjoin="and_(Address.latitude == foreign(RiverRun.put_in_latitude), "
                    "Address.longitude == foreign(RiverRun.put_in_longitude))")

    distance   = Column(Float)
    river_name = Column(String(255))
    run_name   = Column(String(255))

    take_out_latitude  = Column(Float, nullable=False)
    take_out_longitude = Column(Float, nullable=False)
    take_out_address = relationship(
        'Address',
        primaryjoin="and_(Address.latitude == foreign(RiverRun.take_out_latitude), "
                    "Address.longitude == foreign(RiverRun.take_out_longitude))")

    def __repr__(self):
        return 'RiverRun(run_id="%s", run_name="%s")>' % (self.run_id, self.run_name)

    def __str__(self):
        return self.run_name

    @property
    def dict(self):
        """dictionary representation of the river run"""
        return {
            'run_id': self.run_id,
            'class_rating': self.class_rating,
            'max_level': self.max_level,
            'min_level': self.min_level,
            'put_in_latitude': self.put_in_latitude,
            'put_in_longitude': self.put_in_longitude,
            'distance': self.distance,
            'river_name': self.river_name,
            'run_name': self.run_name,
            'take_out_latitude': self.take_out_latitude,
            'take_out_longitude': self.take_out_longitude
        }

    @hybrid_property
    def observed_measurements(self):
        today = datetime.datetime.today()
        predictions = list(self.predictions)

        return [p for p in predictions if p.timestamp <= today]

    @hybrid_property
    def predicted_measurements(self):
        today = datetime.datetime.today()
        predictions = list(self.predictions)

        return [p for p in predictions if p.timestamp > today]

    @hybrid_property
    def todays_runability(self):
        today = datetime.datetime.today()
        predictions = list(self.predictions)

        td = datetime.timedelta(days=1)
        t_prediction = [p for p in predictions if today - td < p.timestamp < today + td]
        if len(t_prediction) == 0 or self.max_level is None or self.min_level is None:
            return -1.
        else:
            p = t_prediction[0]

            midpoint = (self.max_level+self.min_level)/2.
            den = float(self.max_level-midpoint)
            return float(abs(p.fr-midpoint)/den) if den != 0 else -1.

    @property
    def select_option(self):
        return {'label': self.run_name, 'value': self.run_id}


class State(Base):
    """ORM mapping for a state

    Attributes:
        short_name (str): two letter state identification
        long_name (str): full state name
    """
    __tablename__ = 'state'

    short_name = Column(String(2), primary_key=True)
    long_name = Column(String(31))


class Station(Base):
    """ORM mapping for a weather station

    Attributes:
        station_id (string): id
        source (string): the weather station's controlling authority {USGS, NOAA}
        name (string): name
        latitude (float): geographical latitude (DD)
        longitude (float): geographical longitude (DD)
    """
    __tablename__ = 'station'

    __table_args__ = (
        ForeignKeyConstraint(
            ('latitude', 'longitude'),
            ('address.latitude', 'address.longitude')
        ),
    )

    station_id = Column(String(31), primary_key=True)

    source = Column(String(4))
    name   = Column(String(255))
    latitude  = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = relationship(
        'Address',
        primaryjoin="and_(Address.latitude == foreign(Station.latitude), "
                    "Address.longitude == foreign(Station.longitude))")

    def __repr__(self):
        return 'Station(station_id="%s", name="%s", source="%s")>' % \
               (self.station_id, self.name, self.source)

    def __str__(self):
        return self.name

    @property
    def dict(self):
        return {
            'station_id': self.station_id,
            'source': self.source,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude
        }


class StationRiverDistance(Base):
    """ORM mapping describing distances between runs and stations

    Attributes:
        station_id (str): weather station id
        run_id (int): river run id
        put_in_distance (float): distance in miles from put-in to station
        take_out_distance (float): distance in miles from take out-to station
    """
    __tablename__ = 'station_river_distance'

    station_id = Column(ForeignKey('station.station_id'), primary_key=True)
    station = relationship('Station')

    run_id = Column(ForeignKey('river_run.run_id'), primary_key=True)
    distance = Column(Float)

    @hybrid_property
    def source(self):
        """weather station source

        This property is not stored in the backend. It is eager-loaded using a
        join on Station when StationRiverDistance objects are returned from the
        database
        """
        return self.station.source


class TmpMeasurement(Base):
    """ORM mapping for temporary measurements

    Attributes:
        date_time (DateTime): timestamp for when the measurement was taken
        metric_id (int): reference to the metric gathered
        station_id (str): reference to the weather station that gathered the measurement
        value (float): the value recorded
    """
    __tablename__ = "tmp_measurement"

    date_time = Column(DateTime, primary_key=True)

    metric_id = Column(ForeignKey('metric.metric_id'), primary_key=True)
    metric    = relationship('Metric')

    station_id = Column(ForeignKey('station.station_id'), primary_key=True)
    station = relationship('Station')

    value = Column(Float, primary_key=True)
