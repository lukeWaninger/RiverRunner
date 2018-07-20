import os


GEOLOCATION_KEY = os.environ['GEOLOCATION_KEY']
DARK_SKY_KEY    = os.environ['DARK_SKY_KEY']
MAPBOX_KEY      = os.environ['MAPBOX_KEY']

DATABASE = {
   'drivername': os.environ['DB_DRIVER'],
   'host':       os.environ['DB_HOST'],
   'port':       os.environ['DB_PORT'],
   'username':   os.environ['DB_USER'],
   'password':   os.environ['DB_PASS'],
   'database':   os.environ['DB_MAIN']
}


PSYCOPG_DB = {
    'dbname':   DATABASE['database'],
    'user':     DATABASE['username'],
    'password': DATABASE['password'],
    'host':     DATABASE['host'],
    'port':     DATABASE['port']
}
