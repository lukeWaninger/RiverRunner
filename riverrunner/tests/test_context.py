import datetime
import numpy as np
from riverrunner import context
from riverrunner import settings
import time


class TContext(context.Context):
    def __init__(self):
        super().__init__(settings.DATABASE_TEST)
        self.weather_sources = ['NOAA', 'USGS']

    def clear_dependency_data(self, session):
        self.clear_all_tables(session)

        session.query(context.Address).delete()
        session.query(context.State).delete()
        session.commit()

    @staticmethod
    def clear_all_tables(session):
        """ delete all rows from all tables in test database

        :return: None
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
        """ generate a new set of measurements for unit test

        :param i: int, number of measurements to generate
        :param session: context.Session(), the db session for which to pass
                        station and metric dependencies
        :return: list, containing i Measurements
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
        """ generate a new set of measurements for unit test

        :param i: int, number of measurements to generate
        :return: list, containing i Measurements
        """
        return [
            context.Metric(
                metric_id=mid,
                description='a metric description',
                name='some kind of rate of change Copy(%s)' % mid,
                units='thing per second'
            ) for mid in range(i)]

    def get_predictions_for_test(self, i, session):
        """ generate a random set of predictions for unit test

        :param i: int, number of predictions to generate
        :param session: context.Session(), db session for which to
               add prediction dependencies
        :return: list, containing i random predictions
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
        """ generate a random set of runs for unit test

        :param i: int, number of runs to generate
        :param session: context.Session(), database session to query addresses
        :return: list, containing runs
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
        """ generate a random set of stations for unit test

        :param i: int, number of stations to generate
        :param session: context.Session(), database session to query addresses
        :return: list, containing i Stations
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
        """ generate a random latitude

        :return: float, a random latitude
        """
        return np.round(np.random.uniform(46, 49, 1), 3)[0]

    @staticmethod
    def random_longitude():
        """ generate a random longitude

        :return: float, a random longitude
        """
        return np.round(np.random.uniform(-124, -117, 1), 3)[0]
