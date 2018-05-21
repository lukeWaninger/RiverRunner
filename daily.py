import datetime
from riverrunner.context import Context
from riverrunner import continuous_noaa, settings
import sys
import time


def daily_run(attempt=0):
    """input the past 24 hr observations and write to log"""
    try:
        if attempt >= settings.DARK_SKY_RETRIES:
            return 1

        context = Context(settings.DATABASE)
        session = context.Session()

        added = continuous_noaa.put_24hr_observations(session)
        session.close()

        print(f'{datetime.datetime.now().isoformat()}: added {added} observations to db')
        sys.exit(0)
    except Exception as e:
        print(f'{datetime.datetime.now().isoformat()}: failed - {str(e.args)}')
        time.sleep(600)
        daily_run(attempt+1)
        sys.exit(1)


if __name__ == '__main__':
    daily_run(0)