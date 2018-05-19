import datetime
import numpy as np
import psycopg2
from riverrunner import context, settings
import pandas as pd
from riverrunner import context
from riverrunner.context import Address, Measurement, Metric, RiverRun, Station, StationRiverDistance
from riverrunner.repository import Repository
from riverrunner.tests.tcontext import TContext
from unittest import TestCase
from unittest import skip


class TestRepository(TestCase):
    """test class for repository.py

    Attributes:
        context (TContext): mock database context
        session (sqlalchemy.orm.sessionmaker): managed connection to that context
        repo (riverrunner.Repository): class being tested
    """

    @classmethod
    def setUpClass(cls):
        """perform at test class initialization

        Note:
            * ensure only a TContext is used NEVER Context or we'll lose all
            our hard-scraped data
            * any existing data in the mock db will be deleted
            * 5 random addresses are generated because nearly all unittests
            require addresses to exist as a foreign key dependency
        """
        cls.context = TContext()
        cls.session = cls.context.Session()
        cls.repo = Repository(session=cls.session)

        cls.context.clear_dependency_data(cls.session)
        cls.context.generate_addresses(cls.session)

    @classmethod
    def tearDownClass(cls):
        """perform when all tests are complete

        removes all data from the mock database
        """
        cls.context.clear_dependency_data(cls.session)
        cls.session.close()

    def setUp(self):
        """perform before each unittest"""
        self.session.flush()
        self.session.rollback()

    def tearDown(self):
        """perform after each unittest

        clears Prediction, StationRiverDistance, Measurement, Metric
        Station, RiverRun tables
        """
        self.context.clear_all_tables(self.session)

    def test_put_predictions_adds_one(self):
        """test put_predictions can add one prediction"""
        # setup
        predictions = self.context.get_predictions_for_test(1, self.session)

        # assert
        result = self.repo.put_predictions(predictions[0])
        self.assertTrue(result)

    def test_put_predictions_adds_many(self):
        """test put_predictions can add many predictions at once"""
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)

        # assert
        result = self.repo.put_predictions(predictions)
        self.assertTrue(result)

    def test_clear_predictions_empties_table(self):
        """test clearing all predictions from db"""
        # setup
        predictions = self.context.get_predictions_for_test(10, self.session)
        self.repo.put_predictions(predictions)

        # assert
        self.repo.clear_predictions()
        predictions = self.session.query(context.Prediction).all()
        self.assertEqual(len(predictions), 0)

    def test_put_measurements_add_new(self):
        """test put_measurements adds new values"""
        # setup
        self.context.get_measurements_file_for_test(1, self.session)

        # assert
        self.repo.put_measurements(self.context.measurements_file_name)
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 1)

        # tear down
        self.context.remove_measurements_file_for_test()

    def test_put_measurements_overwrite_old(self):
        """test put_measurements overwrites old values"""
        # setup
        self.context.get_measurements_file_for_test(1, self.session)
        self.repo.put_measurements(self.context.measurements_file_name)
        with open(self.context.measurements_file_name, "r") as f:
            measurement = f.readline().strip().split(",")
            new_value = float(measurement[3]) + 1
            measurement[3] = str(new_value)
            new_measurement = "{}\n".format(",".join(measurement))
        with open(self.context.measurements_file_name, "w") as f:
            f.write(new_measurement)

        # assert
        self.repo.put_measurements(self.context.measurements_file_name)
        measurements = self.session.query(context.Measurement).all()
        self.assertEqual(len(measurements), 1)
        self.assertEqual(measurements[0].value, new_value)

        # tear down
        self.context.remove_measurements_file_for_test()

    def test_put_measurements_checks_integrity(self):
        """test put_measurements checks referential integrity"""
        # setup
        self.context.get_measurements_file_for_test(1, self.session)
        self.repo.put_measurements(self.context.measurements_file_name)
        with open(self.context.measurements_file_name, "r") as f:
            measurement = f.readline().strip().split(",")
            measurement[2] = "{}0".format(measurement[2])
            diff_measurement = "{}\n".format(",".join(measurement))
        with open(self.context.measurements_file_name, "w") as f:
            f.write(diff_measurement)

        # assert
        with self.assertRaises(psycopg2.IntegrityError):
            self.repo.put_measurements(self.context.measurements_file_name)
        measurements = self.session.query(context.Measurement).all()
        tmp_measurements = self.session.query(context.TmpMeasurement).all()
        self.assertEqual(len(measurements), 1)
        self.assertEqual(len(tmp_measurements), 0)

        # tear down
        self.context.remove_measurements_file_for_test()

    def test_put_measurements_clears_tmp_measurement_table(self):
        """test put_measurements completes with empty tmp_measurement table"""
        # setup
        self.context.get_measurements_file_for_test(1, self.session)
        self.repo.put_measurements(self.context.measurements_file_name)

        # assert
        tmp_measurements = self.session.query(context.TmpMeasurement).all()
        self.assertEqual(len(tmp_measurements), 0)

        # tear down
        self.context.remove_measurements_file_for_test()

    def test_get_measurements_returns_with_correct_date_range(self):
        """test get_measurements exceptions

        test that the method correctly throws an exception if it's
        given an invalid date range
        """
        # setup
        now = datetime.datetime.now()

        address = self.session.query(Address).first()
        station = Station(
            station_id='1',
            latitude=address.latitude,
            longitude=address.longitude,
            source='NOAA'
        )

        run = RiverRun(
            run_id=1,
            put_in_latitude=address.latitude,
            put_in_longitude=address.longitude,
            class_rating='I',
            max_level=100,
            min_level=10,
            take_out_latitude=address.latitude,
            take_out_longitude=address.longitude,
            distance=10,
            river_name='a river',
            run_name='a run'
        )

        strd = StationRiverDistance(
            station_id=station.station_id,
            run_id=run.run_id,
            distance=1.
        )

        metric = Metric(
            description='a description',
            metric_id=1,
            name='a name',
            units='a scalar'
        )

        self.session.add_all([station, run, strd, metric])

        # ensure the intersection of measurement dates is within a specified date range
        measurements = []
        for i in range(10):
            measurements.append(Measurement(
                station_id=station.station_id,
                metric_id=metric.metric_id,
                date_time=now - datetime.timedelta(days=15, seconds=5*i)
                if i < 5 else now - datetime.timedelta(days=5, seconds=5*i)
            ))
        [self.session.merge(m) for m in measurements]
        self.session.commit()

        # assert
        measurements = self.repo.get_measurements(
            run_id=run.run_id,
            start_date=now - datetime.timedelta(days=16),
            end_date=now - datetime.timedelta(14)
        )

        self.assertEqual(len(measurements), 5)
        for m in measurements.iterrows():
            self.assertTrue(now - datetime.timedelta(days=16) <= m[1].date_time < now - datetime.timedelta(days=14))

    def test_get_measurements_throws_if_start_is_later_than_end(self):
        """test get_measurements exceptions

        test that the method correctly throws an exception if it's
        given an invalid date range
        """
        # setup
        runs = self.context.get_runs_for_test(1, self.session)
        self.session.add_all(runs)

        # assert
        now = datetime.datetime.now()
        self.assertRaises(ValueError, self.repo.get_measurements,
                          run_id=runs[0].run_id,
                          start_date=now - datetime.timedelta(days=10),
                          end_date=now - datetime.timedelta(days=15))

    def test_get_measurements_throws_if_start_is_later_than_today(self):
        """test get_measurements exceptions

        test that the method correctly throws an exception if it's
        given an invalid date range
        """
        # setup
        runs = self.context.get_runs_for_test(1, self.session)
        self.session.add_all(runs)

        # assert
        now = datetime.datetime.now()
        self.assertRaises(ValueError, self.repo.get_measurements,
                          run_id=runs[0].run_id,
                          start_date=now + datetime.timedelta(days=10))

    def test_get_measurements_throws_if_run_id_does_not_exist_neg(self):
        """test get_measurements exceptions

        test that the method will throw an error when a given run
        id does not exist in the db and the given id is negative
        """
        # assert
        self.assertRaises(ValueError, self.repo.get_measurements,
                          run_id=-1)

    def test_get_measurements_throws_if_run_id_does_not_exist_pos(self):
        """test get_measurements exceptions

        test that the method will throw an error when a given run
        id does not exist in the db and the given id is positive
        """
        # setup
        rids = [r.run_id for r in self.repo.get_all_runs()]
        rid  = 0
        while rid in rids:
            rid += 1

        # assert
        self.assertRaises(ValueError, self.repo.get_measurements,
                          run_id=rid)

    def test_get_measurements_returns_past_thirty_if_no_date_range_is_given(self):
        """test get_measurements behavior

        test that the method returns only the past thirty days
        if no date range is given as a calling argument
        """
        # setup
        now = datetime.datetime.now()

        address = self.session.query(Address).first()
        station = Station(
            station_id='1',
            latitude=address.latitude,
            longitude=address.longitude,
            source=self.context.weather_sources[0]
        )

        run = RiverRun(
            run_id=1,
            put_in_latitude=address.latitude,
            put_in_longitude=address.longitude,
            class_rating='I',
            max_level=100,
            min_level=10,
            take_out_latitude=address.latitude,
            take_out_longitude=address.longitude,
            distance=10,
            river_name='a river',
            run_name='a run'
        )

        strd = StationRiverDistance(
            station_id=station.station_id,
            run_id=run.run_id,
            distance=1.
        )

        metric = Metric(
            description='a description',
            metric_id=1,
            name='a name',
            units='a scalar'
        )

        self.session.add_all([station, run, strd, metric])

        measurements = []
        for i in range(10):
            measurements.append(
                Measurement(
                    station_id=station.station_id,
                    metric_id=metric.metric_id,
                    date_time=now - datetime.timedelta(days=45, seconds=5*i)
                    if i < 5 else now - datetime.timedelta(days=5, seconds=5*i)
            ))

        [self.session.merge(m) for m in measurements]
        self.session.commit()

        # assert
        measurements = self.repo.get_measurements(run_id=run.run_id)

        self.assertEqual(len(measurements), 5)
        for m in measurements.iterrows():
            self.assertTrue(m[1].date_time >= now - datetime.timedelta(30))

    def test_get_measurements_returns_from_more_than_one_station(self):
        """test that more than one station is return when necessary"""
        # setup
        now = datetime.datetime.now()

        addresses = self.session.query(Address).limit(2)
        stations = [
            Station(
                station_id='1',
                latitude=addresses[0].latitude,
                longitude=addresses[0].longitude,
                source=self.context.weather_sources[0]
            ),
            Station(
                station_id='2',
                latitude=addresses[1].latitude,
                longitude=addresses[1].longitude,
                source=self.context.weather_sources[1]
            )
        ]

        run = RiverRun(
            run_id=1,
            put_in_latitude=addresses[0].latitude,
            put_in_longitude=addresses[0].longitude,
            class_rating='I',
            max_level=100,
            min_level=10,
            take_out_latitude=addresses[1].latitude,
            take_out_longitude=addresses[1].longitude,
            distance=10,
            river_name='a river',
            run_name='a run'
        )

        strds = [
            StationRiverDistance(
                station_id=s.station_id,
                run_id=run.run_id,
                distance=1.
            )
            for s in stations
        ]

        metric = Metric(
            description='a description',
            metric_id=1,
            name='a name',
            units='a scalar'
        )

        self.session.add_all(stations)
        self.session.add(run)
        self.session.add_all(strds)
        self.session.add(metric)

        measurements = []
        for i in range(10):
            measurements.append(
                Measurement(
                    station_id=stations[i % 2].station_id,
                    metric_id=metric.metric_id,
                    date_time=now - datetime.timedelta(days=15, seconds=5*i)
                )
            )

        [self.session.merge(m) for m in measurements]
        self.session.commit()

        # assert
        measurements = self.repo.get_measurements(run_id=run.run_id, min_distance=100.)
        self.assertEqual(len(measurements), 10)

    def test_get_measurements_returns_all_sources(self):
        # setup
        now = datetime.datetime.now()

        addresses = self.session.query(Address).limit(3)
        stations = [
            Station(
                station_id=str(i),
                latitude=addresses[i].latitude,
                longitude=addresses[i].longitude,
                source=self.context.weather_sources[i]
            )
            for i in range(len(self.context.weather_sources))
        ]

        run = RiverRun(
            run_id=1,
            put_in_latitude=addresses[0].latitude,
            put_in_longitude=addresses[0].longitude,
            class_rating='I',
            max_level=100,
            min_level=10,
            take_out_latitude=addresses[1].latitude,
            take_out_longitude=addresses[1].longitude,
            distance=10,
            river_name='a river',
            run_name='a run'
        )

        strds = [
            StationRiverDistance(
                station_id=s.station_id,
                run_id=run.run_id,
                distance=1.
            )
            for s in stations
        ]

        metric = Metric(
            description='a description',
            metric_id=1,
            name='a name',
            units='a scalar'
        )

        self.session.add_all(stations)
        self.session.add(run)
        self.session.add_all(strds)
        self.session.add(metric)

        measurements = []
        for i in range(10):
            measurements.append(
                Measurement(
                    station_id=stations[i % len(stations)].station_id,
                    metric_id=metric.metric_id,
                    date_time=now - datetime.timedelta(days=15, seconds=5 * i)
                )
            )

        [self.session.merge(m) for m in measurements]
        self.session.commit()

        # assert
        measurements = self.repo.get_measurements(run_id=run.run_id)
        self.assertTrue(set(self.context.weather_sources) == set(measurements.source.values))

    def test_get_all_runs(self):
        """test whether all runs are returned"""
        # setup
        runs = self.context.get_runs_for_test(2, self.session)
        self.session.add_all(runs)

        # assert
        runs = self.repo.get_all_runs()
        self.assertEqual(len(runs), 2)

    def test_get_all_stations(self):
        """test whether all stations are returned"""
        # setup
        stations = self.context.get_stations_for_test(10, self.session)
        self.session.add_all(stations)

        # assert
        stations = self.repo.get_all_stations()
        self.assertEqual(len(stations), 10)

    def put_station_river_distances(self):
        """test whether station river distances persists to db"""
        # setup
        stations = self.context.get_stations_for_test(10, self.session)
        runs = self.context.get_runs_for_test(10, self.session)

        self.session.add_all(stations)
        self.session.add_all(runs)
        self.session.commit()
        
        # assert
        strds = [
            StationRiverDistance(
                station_id=stations[np.random.randint(0, len(stations))].station_id,
                run_id=runs[np.random.randint(0, len(runs))].run_id,
                distance=4
            )
            for i in range(10)
        ]

        strds = self.repo.put_station_river_distances(strds)
        strds = self.session.query(StationRiverDistance).all()

        self.assertEqual(len(strds), 10)

    @skip("passed 15 May 18, test takes ~50seconds so skip")
    def test_get_measurements_specific_range_1(self):
        """unittest for specific range

        test whether a given date range is returning all sources
        and all measurements [2009-01-01, 2016, 01, 01] | run_id=500
        """

        # setup
        addresses = self.session.query(Address).all()
        stations = []
        for i in range(100):
            soid = i % len(self.context.weather_sources)
            aid  = i % len(addresses)

            stations.append(Station(
                station_id=str(i),
                latitude=addresses[aid].latitude,
                longitude=addresses[aid].longitude,
                source=self.context.weather_sources[soid]
            ))

        runs = []
        for i in range(300, 600):
            pid = np.random.randint(0, 997) % len(addresses)
            tid = np.random.randint(0, 997) % len(addresses)

            runs.append(
                RiverRun(
                    run_id=i,
                    put_in_latitude=addresses[pid].latitude,
                    put_in_longitude=addresses[pid].longitude,
                    class_rating='I',
                    max_level=100,
                    min_level=10,
                    take_out_latitude=addresses[tid].latitude,
                    take_out_longitude=addresses[tid].longitude,
                    distance=10,
                    river_name=f'a river {i}',
                    run_name=f'a run {i}'
                )
            )

        strds, stations_per_run = [], 4  # four to ensure all sources exist for each run
        for r in runs:
            spr = stations_per_run
            sidx = np.random.randint(0, len(stations)-4)

            for s in stations[sidx: sidx + stations_per_run]:

                d = ((s.latitude-r.put_in_latitude)**2+(s.longitude-r.put_in_longitude)**2)**.5
                strds.append(
                    StationRiverDistance(
                        station_id=s.station_id,
                        run_id=r.run_id,
                        distance=d
                    )
                )
                spr -= 1
                if spr == 0:
                    break

        metric_names = [
            'Streamflow',
            'Sensor Depth',
            'Water Velocity',
            'Precipitation (USGS)',
            'Temperature (USGS)',
            'Precipitation (NOAA)',
            'Precipitation (USGS)',
            'Snowpack'
        ]
        metrics = []
        for i, n in enumerate(metric_names):
            metrics.append(
                Metric(
                    description='a description',
                    metric_id=i,
                    name=n,
                    units='a scalar'
                )
            )

        self.session.add_all(stations)
        self.session.add_all(runs)
        self.session.add_all(strds)
        self.session.add_all(metrics)
        self.session.commit()

        measurements = []
        day, start, end = -10, datetime.datetime(2009, 1, 1), datetime.datetime(2016, 1, 1)
        quit = end + datetime.timedelta(days=10)

        while True:
            md = start + datetime.timedelta(days=day)

            measurements.append(
                Measurement(
                    station_id=stations[day % len(stations)].station_id,
                    metric_id=metrics[day % len(metrics)].metric_id,
                    date_time=md,
                    value=day
                )
            )

            day += 1
            if md >= quit:
                break

        [self.session.merge(m) for m in measurements]
        self.session.commit()

        # assert
        measurements = self.repo.get_measurements(run_id=500, start_date=start, end_date=end)

        for m in measurements.iterrows():
            self.assertTrue(start <= m[1].date_time < end)

        self.assertTrue(set(self.context.weather_sources) == set(measurements.source.values))
