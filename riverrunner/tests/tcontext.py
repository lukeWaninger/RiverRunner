import datetime
import numpy as np
from riverrunner import context
from riverrunner import settings
import time


class TContext(context.Context):
    """mock database context

    generates a mock database context for unit testing

    Attributes:
        weather_sources ([str]): list of possible weather sources
    """
    def __init__(self):
        super().__init__(settings.DATABASE_TEST)
        self.weather_sources = ['NOAA', 'USGS', 'SNOW']

    def clear_dependency_data(self, session):
        """clear all data from mock db

        Args:
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Returns:
            None
        """
        self.clear_all_tables(session)

        session.query(context.Address).delete()
        session.query(context.State).delete()
        session.commit()

    @staticmethod
    def clear_all_tables(session):
        """clear tables for unittest tear down

        it is important that order of entities below remain in this order.
        if not, the SQL statements will not complete from foreign key
        dependency issues

        Args:
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Returns:
            None
        """
        entities = [
            context.Prediction,
            context.StationRiverDistance,
            context.Measurement,
            context.Metric,
            context.Station,
            context.RiverRun
        ]

        for entity in entities:
            session.query(entity).delete()
        session.commit()

    def generate_addresses(self, session):
        """generate a random set of addresses

        generates and inserts a random set of addresses into the db

        Args:
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Returns:
            None
        """
        # fill a few foreign key dependencies
        session.add(context.State(
            short_name='WA',
            long_name='Washington'
        ))

        addresses = [
            context.Address(
                latitude=self.random_latitude(),
                longitude=self.random_longitude(),
                address='that street you know somewhere',
                city='a city %s' % i,
                county='King',
                state='WA',
                zip='a zip'
            )
            for i in range(5)
        ]
        session.add_all(addresses)
        session.commit()

    def get_measurements_for_test(self, i, session):
        """generate a random set of measurements

        Args:
            i (int): number of measurements to generate
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Return:
             [Measurement]: list containing i random Measurements
        """
        stations = self.get_stations_for_test(i, session)
        session.add_all(stations)

        metrics = self.get_metrics_for_test(i)
        session.add_all(metrics)

        session.commit()

        measurements = []
        for idx in range(i):
            measurements.append(
                context.Measurement(
                    station_id=np.random.choice(stations, 1)[0].station_id,
                    metric_id=np.random.choice(metrics, 1)[0].metric_id,
                    date_time=datetime.datetime.now(),
                    value=np.round(np.random.normal(10, 3, 1)[0], 3)
                ))

            # make sure we don't generate duplicate keys
            time.sleep(.001)

        return measurements

    @staticmethod
    def get_metrics_for_test(i):
        """generate a random set of metrics

        Args:
            i (int): number of measurements to generate

        Return:
            [Metric]: list containing i random Measurements
        """
        return [
            context.Metric(
                metric_id=mid,
                description='a metric description',
                name='some kind of rate of change Copy(%s)' % mid,
                units='thing per second'
            ) for mid in range(i)]

    def get_predictions_for_test(self, i, session):
        """generate a random set of predictions

        Args:
            i (int): number of predictions to generate
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Return:
            [Prediction]: list containing i random predictions
        """
        runs = self.get_runs_for_test(i, session)
        session.add_all(runs)
        session.commit()

        predictions = []
        for idx in range(i):
            fr = np.random.uniform(100, 1000, 1)[0]
            sd = np.random.normal(50, 10, 1)[0]

            predictions.append(
                context.Prediction(
                    run_id=np.random.choice(runs, 1)[0].run_id,
                    timestamp=datetime.datetime.now(),
                    fr_lb=np.round(fr - sd, 1),
                    fr=np.round(fr, 1),
                    fr_ub=np.round(fr + sd, 1)
                )
            )

            # make sure we don't generate duplicate keys
            time.sleep(.001)

        return predictions

    @staticmethod
    def get_runs_for_test(i, session):
        """generate a random set of runs

        Args:
            i (int): number of runs to generate
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Returns:
            [RiverRun]: list containing i random runs
        """
        addresses = session.query(context.Address).all()
        runs = []
        for idx in range(i):
            put_in = np.random.choice(addresses, 1)[0]
            take_out = np.random.choice(addresses, 1)[0]

            runs.append(context.RiverRun(
                run_id=idx,
                class_rating=np.random.choice(['I', 'II', 'IV', 'V', 'GTFO'], 1)[0],
                min_level=int(np.random.randint(0, 100, 1)[0]),
                max_level=int(np.random.randint(100, 1000, 1)[0]),
                put_in_latitude=put_in.latitude,
                put_in_longitude=put_in.longitude,
                distance=np.round(np.random.uniform(5, 3, 1)[0], 1),
                take_out_latitude=take_out.latitude,
                take_out_longitude=take_out.longitude
            ))

        return runs

    @staticmethod
    def get_stations_for_test(i, session):
        """generate a random set of weather stations

        Args:
            i (int): number of stations to generate
            session (sqlalchemy.orm.sessionmaker): managed connection to mock db

        Returns:
            [Station]: list containing i random stations
        """
        addresses = session.query(context.Address).all()

        stations = []
        for sid in range(i):
            address = np.random.choice(addresses, 1)[0]

            stations.append(context.Station(
                station_id=str(int(sid)),
                source=np.random.choice(['NOAA', 'USGS'], 1)[0],
                name='station %s' % sid,
                latitude=address.latitude,
                longitude=address.longitude
            ))

        return stations

    @staticmethod
    def random_latitude():
        """generate a random latitude

        Returns:
            float: a random latitude within the state of Washington
        """
        return np.round(np.random.uniform(46, 49, 1), 3)[0]

    @staticmethod
    def random_longitude():
        """generate a random longitude

        Returns:
            float: a random longitude within the state of Washington
        """
        return np.round(np.random.uniform(-124, -117, 1), 3)[0]
