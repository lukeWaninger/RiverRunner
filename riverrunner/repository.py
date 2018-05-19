import datetime
import pandas as pd
import psycopg2
from riverrunner import context
from riverrunner.context import Measurement, Prediction, RiverRun, Station, StationRiverDistance
from riverrunner import settings
from sqlalchemy.exc import SQLAlchemyError


class Repository:
    """interface between application and backend

    """
    def __init__(self, session=None, connection=None):
        if session is None:
            self.__context = context.Context(settings.DATABASE)
            self.__session = self.__context.Session()
        else:
            self.__session = session

        if connection is None:
            self.__connection = psycopg2.connect(**settings.PSYCOPG_DB)
        else:
            self.__connection = connection

    def __del__(self):
        self.__session.flush()
        self.__session.close()
        self.__connection.close()

    def put_predictions(self, predictions):
        """add a set of predictions

        Note
            session will rollback transaction if commit fails

        Args
            predictions ([Prediction]): set of predictions to insert

        Returns
            bool: success/fail

        Raises
             TypeError: if predictions is not a list
        """
        if not type(predictions) is list:
            predictions = [predictions]

        try:
            self.__session.add_all(predictions)
            self.__session.commit()

            return True
        except:
            self.__session.rollback()

            return False

    def clear_predictions(self):
        """delete all existing predictions from database

        Returns
         None
        """
        self.__session.query(Prediction).delete()

    def put_measurements_from_csv(self, csv_file):
        """ add a file of measurements

        Notes:
            * will overwrite previous values with same primary key
            * connection will rollback transaction if commit fails

        Args:
            csv_file (file): name of file containing records to insert

        Returns:
            bool: success/exception

        Raises:
            Exception: if error occurs while connected to database
        """
        try:
            with self.__connection.cursor() as cursor:
                with open(csv_file, "r") as f:
                    cursor.copy_from(f, "tmp_measurement", sep=",")
                cursor.execute("""
                    INSERT into measurement
                        SELECT * FROM tmp_measurement
                    ON CONFLICT (station_id, metric_id, date_time)
                        DO UPDATE SET value = EXCLUDED.value;
                """)
                cursor.execute("""
                    DELETE FROM tmp_measurement;
                """)

            self.__connection.commit()

            return True
        except:
            self.__connection.rollback()

            raise

    def put_measurements_from_list(self, measurements):
        """add a list of measurements to the database

        Args
            measurements [Measurement]: list of measurements to put in the db

        Returns
            None
        """
        try:
            self.__session.add_all(measurements)
            self.__session.commit()
        except SQLAlchemyError as e:
            print([str(a) for a in e.args])
            self.__session.rollback()
            raise e

    def get_measurements(self, run_id, start_date=None, end_date=None, min_distance=0.):
        """ get a set of measurements from the db

        * not supplying a start and end date will return measurements covering the previous 30 days. add a start date to retrieve older
        * supplying a start date without and end date will pull all measurements up to the current day
        * if no min distance (or a negative distance) is provided the method will return measurements associated with the closest weather station from each unique source
        * supplying a distance will NOT guarantee both NOAA and USGS stations are retrieved
        * supplying an end date without a start will raise an exception
        * supplying an end date earlier than the start will raise an exception

        Args:
            run_id (int): retrieve measurements associated with a specific run
            start_date (DateTime) - optional: beginning of date range for which to retrieve measurements. if None is
            supplied the function will default to retrieving the past thirty days
            end_date (DateTime) - optional: end of date range for which to retrieve measurements
            min_distance (float): distance from run for which to retrieve measurements

        Returns:
            DataFrame: containing measurements within the given set of parameters

        Raises:
             ValueError: if start date is later than end date
             ValueError: if start date is is later than current date
             ValueError: if end date is supplied without a starting date
        """
        # ensure dates are correct
        if start_date is not None:
            if start_date > datetime.datetime.now():
                raise ValueError('start date cannot be later than today')

            if end_date is not None and end_date < start_date:
                raise ValueError('end date cannot be before start date')
        else:
            start_date = datetime.datetime.now() - datetime.timedelta(days=30)

        if end_date is None:
            end_date = datetime.datetime.now()

        # ensure the run_id exists if it was supplied
        def raise_rid_error():
            raise ValueError('run_id does not exist: %s' % run_id)

        if run_id > -1:
            try:
                run = self.__session.query(RiverRun.run_id).filter(RiverRun.run_id == run_id).first()
                if run is None:
                    raise_rid_error()
            except Exception as e:
                raise_rid_error()
        else:
            raise_rid_error()

        # define the stations we need to reference
        stations = self.__session.query(StationRiverDistance.station_id,
                                        StationRiverDistance.distance,
                                        Station.source)\
            .join(Station, (Station.station_id == StationRiverDistance.station_id))\
            .filter(StationRiverDistance.run_id == run_id)\
            .order_by(StationRiverDistance.distance)\
            .all()

        # make sure at least one of each weather source is returned
        if min_distance <= 0.:
            tmp = []
            noaa, usgs, snow = False, False, False
            for station in stations:
                if 'NOAA' == station[2]:
                    tmp.append(station)
                    noaa = True
                elif 'USGS' == station[2]:
                    tmp.append(station)
                    usgs = True
                elif 'SNOW' == station[2]:
                    tmp.append(station)
                    snow = True
                if noaa and usgs and snow:
                    break

            stations = tmp
        else:
            stations = [s for s in stations if s[1] < min_distance]

        station_ids = [s[0] for s in stations]

        # make the query
        measurements = self.__session.query(Measurement)\
            .filter(Measurement.station_id.in_(station_ids),
                    Measurement.date_time >= start_date,
                    Measurement.date_time < end_date)\
            .all()

        df = pd.DataFrame([m.dict for m in measurements])
        return df

    def get_all_runs(self):
        """retrieve all runs from db

        Returns
            DataFrame: containing all runs
        """

        runs = pd.DataFrame([r.dict for r in self.__session.query(RiverRun).all()])
        return runs

    def get_all_stations(self):
        """retrieve all weather stations from db

        Returns:
            DataFrame: containing all weather stations
        """

        stations = pd.DataFrame([s.dict for s in self.__session.query(Station).all()])
        return stations

    def put_station_river_distances(self, strd):
        """put station river distance objects in the db

        Args:
            strd ([StationRiverDistance]): list of StationRiverDistances to add
        """
        if not type(strd) is list:
            strd = [strd]

        try:
            self.__session.add_all(strd)
            self.__session.commit()

            return True
        except Exception as e:
            self.__session.rollback()

            return False

    def get_run(self, run_id):
        """retrieve a single run

        Args
            run_id (int): run id
        """
        if run_id < 0:
            raise ValueError('run id does not exist')
        else:
            pass

        try:
            run = self.__session.query(RiverRun).filter(RiverRun.run_id == run_id).scalar()

            if run is None:
                raise ValueError('run id does not exist')

            return run
        except SQLAlchemyError as e:
            print([str(a) for a in e.args])
            raise e
